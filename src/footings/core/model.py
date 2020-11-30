from functools import partial
from inspect import signature
import sys
from traceback import extract_tb, format_list
from typing import List, Optional

from attr import attrs, attrib
from attr._make import _CountingAttr
from attr.setters import frozen
import numpydoc.docscrape as numpydoc

from .attributes import Parameter, Modifier, Meta, Placeholder, Asset
from .audit import run_model_audit
from ..doc_tools.docscrape import FootingsDoc
from .visualize import visualize_model


class ModelRunError(Exception):
    """Error occured during model run."""


class ModelCreationError(Exception):
    """Error occured creating model object."""


def _run(self, to_step):

    if to_step is None:
        steps = self.__footings_steps__
    else:
        try:
            position = self.__footings_steps__.index(to_step)
            steps = self.__footings_steps__[: (position + 1)]
        except ValueError as e:
            msg = f"The step passed to to_step '{to_step}' does not exist as a step."
            raise e(msg)

    def _run_step(step):
        try:
            return getattr(self, step)()
        except:
            exc_type, exc_value, exc_trace = sys.exc_info()
            msg = f"At step [{step}], an error occured.\n"
            msg += f"  Error Type = {exc_type.__name__}\n"
            msg += f"  Error Message = {exc_value}\n"
            msg += f"  Error Trace = {format_list(extract_tb(exc_trace))}\n"
            raise ModelRunError(msg)

    for step in steps:
        _run_step(step)

    if to_step is not None:
        return self
    if len(self.__footings_assets__) > 1:
        return tuple(getattr(self, asset) for asset in self.__footings_assets__)
    return getattr(self, self.__footings_assets__[0])


@attrs(slots=True, repr=False)
class Footing:
    """The parent modeling class providing the key methods of run, audit, and visualize."""

    __footings_steps__: tuple = attrib(init=False, repr=False)
    __footings_parameters__: tuple = attrib(init=False, repr=False)
    __footings_modifiers__: tuple = attrib(init=False, repr=False)
    __footings_meta__: tuple = attrib(init=False, repr=False)
    __footings_placeholders__: tuple = attrib(init=False, repr=False)
    __footings_assets__: tuple = attrib(init=False, repr=False)

    def _combine_attributes(self):
        def _format(x):
            if x[-1] == "s":
                return x[:-1]
            return x

        srcs = ["parameters", "modifiers", "meta", "placeholders", "assets"]
        return {
            a: f"{_format(src)}.{a}"
            for src in srcs
            for a in getattr(self, f"__footings_{src}__")
        }

    def visualize(self):
        """Visualize the model to get an understanding of what model attributes are used and when."""
        return visualize_model(self)

    def audit(self, file: str, **kwargs):
        """Audit the model which returns copies of the object as it is modified across each step.

        Parameters
        ----------
        file : str
            The name of the audit file.
        kwargs
            Additional key words passed to audit.

        Returns
        -------
        None
            An audit file in specfified format (e.g., .xlsx).
        """
        return run_model_audit(model=self, file=file, **kwargs)

    def run(self, to_step=None):
        """Runs the model and returns any assets defined.

        Parameters
        ----------
        to_step : str
            The name of the step to run model to.

        """
        return _run(self, to_step=to_step)


@attrs(frozen=True, slots=True)
class Step:
    name = attrib(type=str)
    docstring = attrib(type=str)
    method = attrib(type=callable)
    method_name = attrib(type=str)
    uses = attrib(type=List[str])
    impacts = attrib(type=List[str])
    metadata = attrib(type=dict, factory=dict)

    @classmethod
    def create(
        cls,
        method: callable,
        uses: List[str],
        impacts: List[str],
        name: Optional[str] = None,
        docstring: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        method_name = method.__qualname__.split(".")[1]
        return cls(
            name=name if name is not None else method_name,
            docstring=docstring if docstring is not None else method.__doc__,
            method=method,
            method_name=method_name,
            uses=uses,
            impacts=impacts,
            metadata={} if metadata is None else metadata,
        )

    def __doc__(self):
        return self.docstring

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)


def step(
    method: callable = None,
    *,
    uses: List[str],
    impacts: List[str],
    name: str = None,
    docstring: str = None,
    metadata: dict = None,
):
    """Turn a method into a step within the footings framework.

    Parameters
    ----------
    method : callable, optional
        The method to decorate, by default None.
    uses : List[str]
        A list of the object names used by the step.
    impacts : List[str]
        A list of the object names that are impacted by the step (i.e., the assets and placeholders).
    wrap : callable, optional
        Wrap or source the docstring from another object, by default None.

    Returns
    -------
    callable
        The decorated method with a attributes for uses and impacts and updated docstring if wrap passed.
    """
    if method is None:
        return partial(
            step,
            uses=uses,
            impacts=impacts,
            name=name,
            docstring=docstring,
            metadata=metadata,
        )

    return Step.create(
        method=method,
        uses=uses,
        impacts=impacts,
        name=name,
        docstring=docstring,
        metadata=metadata,
    )


def _make_doc_parameter(attribute):
    str_type = str(attribute.type) if attribute.type is not None else ""
    return numpydoc.Parameter(
        attribute.name, str_type, [attribute.metadata.get("description", "")]
    )


def _parse_attriubtes(cls):
    sections = ["Parameters", "Modifiers", "Meta", "Placeholders", "Assets"]
    parsed_attributes = {section: [] for section in sections}

    for attribute in cls.__attrs_attrs__:
        grp = attribute.metadata.get("footing_group", None)
        if isinstance(grp, Parameter):
            parsed_attributes["Parameters"].append(_make_doc_parameter(attribute))
        elif isinstance(grp, Modifier):
            parsed_attributes["Modifiers"].append(_make_doc_parameter(attribute))
        elif isinstance(grp, Meta):
            parsed_attributes["Meta"].append(_make_doc_parameter(attribute))
        elif isinstance(grp, Placeholder):
            parsed_attributes["Placeholders"].append(_make_doc_parameter(attribute))
        elif isinstance(grp, Asset):
            parsed_attributes["Assets"].append(_make_doc_parameter(attribute))

    return parsed_attributes


def _update_run_return(cls, assets):
    run_doc = numpydoc.FunctionDoc(cls.run)

    if cls._return.__doc__ is not None:
        return_doc = numpydoc.FunctionDoc(cls._return)
        run_doc["Returns"] = return_doc["Returns"]
    else:
        run_doc["Returns"] = assets

    return str(run_doc)


def _generate_steps_sections(cls, steps):
    return [
        f"{idx}. {step} - {getattr(cls, step).docstring}"
        for idx, step in enumerate(steps, start=1)
    ]


def _attr_doc(cls, steps):

    parsed_attributes = _parse_attriubtes(cls)
    doc = FootingsDoc(cls)

    doc["Parameters"] = parsed_attributes["Parameters"]
    doc["Modifiers"] = parsed_attributes["Modifiers"]
    doc["Meta"] = parsed_attributes["Meta"]
    doc["Placeholders"] = parsed_attributes["Placeholders"]
    doc["Assets"] = parsed_attributes["Assets"]
    doc["Steps"] = _generate_steps_sections(cls, steps)
    doc["Methods"] = []

    cls.__doc__ = str(doc)
    return cls


def _prepare_signature(cls):
    old_sig = signature(cls)
    return old_sig.replace(return_annotation=f"{cls.__name__}")


def model(cls: type = None, *, steps: List[str]):
    """Turn a class into a model within the footings framework.

    Parameters
    ----------
    cls : type
        The class to turn into a model.
    steps : List[str]
        The list of steps to the model.

    Returns
    -------
    cls
        Returns cls as a model within footings framework.
    """
    if cls is None:
        return partial(model, steps=steps)

    def inner(cls):
        # In order to be instantiated as a model, need to pass the following test.

        # 1. Needs to be a subclass of Footing
        if issubclass(cls, Footing) is False:
            raise ModelCreationError(
                f"The object {str(cls)} is not a child of the Footing class."
            )

        # 2. All attributes need to belong to a footings_group
        exclude = [x for x in dir(Footing) if x[0] != "_"]
        attributes = [x for x in dir(cls) if x[0] != "_" and x not in exclude]
        if hasattr(cls, "__attrs_attrs__"):
            attrs_attrs = {x.name: x for x in cls.__attrs_attrs__}
        parameters, modifiers, meta, placeholders, assets = [], [], [], [], []
        for attribute in attributes:
            attr = getattr(cls, attribute)
            if attribute in attrs_attrs:
                attr = attrs_attrs[attribute]
            else:
                if isinstance(attr, _CountingAttr) is False:
                    msg = f"The attribute {attribute} is not registered to a known Footings group.\n"
                    msg += "Use one of define_parameter, define_meta, define_modifier, define_placeholder "
                    msg += "or define_asset when building a model."
                    raise ModelCreationError(msg)
            footing_group = attr.metadata.get("footing_group", None)
            if footing_group is None:
                msg = f"The attribute {attribute} is not registered to a known Footings group.\n"
                msg += "Use one of define_parameter, define_meta, define_modifier or define_asset "
                msg += "when building a model."
                raise ModelCreationError(msg)
            if isinstance(footing_group, Parameter):
                parameters.append(attribute)
            elif isinstance(footing_group, Modifier):
                modifiers.append(attribute)
            elif isinstance(footing_group, Meta):
                meta.append(attribute)
            elif isinstance(footing_group, Placeholder):
                placeholders.append(attribute)
            elif isinstance(footing_group, Asset):
                assets.append(attribute)

        # 3. Make sure at least one asset
        if len(assets) == 0:
            raise ModelCreationError(
                "No assets registered to model. At least one asset needs to be registered."
            )

        # 4. For steps -
        #    - make sure at least one step in model
        #    - all steps are methods of cls
        #    - all steps have attributes uses and impacts
        if len(steps) == 0:
            raise ModelCreationError("Model needs to have at least one step.")
        missing_steps = []
        missing_attributes = []
        for step_nm in steps:
            step = getattr(cls, step_nm, None)
            if step is None:
                missing_steps.append(step_nm)
            if hasattr(step, "uses") is False or hasattr(step, "impacts") is False:
                missing_attributes.append(step_nm)
        if len(missing_steps) > 0:
            raise ModelCreationError(
                f"The following steps listed are missing - {str(missing_steps)} from the object."
            )
        if len(missing_attributes) > 0:
            raise ModelCreationError(
                f"The followings steps listed do not appear to be decorated steps - {str(missing_attributes)}."
            )

        # If all test pass, update steps and assets with known values as defaults.
        kws = {"init": False, "repr": False}
        cls.__footings_steps__ = attrib(default=tuple(steps), **kws)
        cls.__footings_parameters__ = attrib(default=tuple(parameters), **kws)
        cls.__footings_modifiers__ = attrib(default=tuple(modifiers), **kws)
        cls.__footings_meta__ = attrib(default=tuple(meta), **kws)
        cls.__footings_placeholders__ = attrib(default=tuple(placeholders), **kws)
        cls.__footings_assets__ = attrib(default=tuple(assets), **kws)

        # Make attrs dataclass and update signature
        cls = attrs(
            maybe_cls=cls, kw_only=True, on_setattr=frozen, repr=False, slots=True
        )
        cls.__signature__ = _prepare_signature(cls)
        return _attr_doc(cls, steps)

    return inner(cls)
