import importlib
import pathlib
import types
import uqbar  # noqa
from typing import List, MutableMapping, Sequence, Tuple, Type  # noqa
from uqbar.apis.ClassDocumenter import ClassDocumenter
from uqbar.apis.FunctionDocumenter import FunctionDocumenter
from uqbar.apis.MemberDocumenter import MemberDocumenter


class ModuleDocumenter:
    """
    A basic module documenter.

    ::

        >>> import uqbar.apis
        >>> documenter = uqbar.apis.ModuleDocumenter(
        ...     'uqbar.io',
        ...     module_documenters=[
        ...         uqbar.apis.ModuleDocumenter('uqbar.io.Timer'),
        ...         ],
        ...     )
        >>> print(str(documenter))
        .. _uqbar--io:
        <BLANKLINE>
        io
        ==
        <BLANKLINE>
        .. automodule:: uqbar.io
        <BLANKLINE>
        .. currentmodule:: uqbar.io
        <BLANKLINE>
        .. toctree::
        <BLANKLINE>
           Timer
        <BLANKLINE>
        .. autofunction:: find_common_prefix
        <BLANKLINE>
        .. autofunction:: relative_to
        <BLANKLINE>
        .. autofunction:: walk
        <BLANKLINE>
        .. autofunction:: write

    .. tip::

       Subclass :py:class:`~uqbar.apis.ModuleDocumenter` to implement your own
       custom module documentation output.
       You'll need to provide your desired reStructuredText output
       via an overridden
       :py:meth:`~uqbar.apis.ModuleDocumenter.ModuleDocumenter.__str__`
       implementation.

       See :py:class:`~uqbar.apis.SummarizingModuleDocumenter` for an example.

    :param package_path: the module path of the module to document
    :param document_private_members: whether to documenter private module members
    :param member_documenter_classes: a list of
        :py:class:`~uqbar.apis.MemberDocumenter` subclasses, defining what classes
        to use to identify and document module members
    :param module_documenters: a list of of documenters for submodules and
        subpackages of the documented module; these are generated by an
        :py:class:`~uqbar.apis.APIBuilder` instance rather than the module
        documenter directly
    :param api_builder: an :py:class:`~uqbar.apis.APIBuilder` instance
    """

    ### CLASS VARIABLES ###

    __documentation_section__ = 'Documenters'

    ### INITIALIZER ###

    def __init__(
        self,
        package_path: str,
        document_private_members: bool=False,
        member_documenter_classes: Sequence[Type[MemberDocumenter]]=None,
        module_documenters: Sequence['ModuleDocumenter']=None,
        ) -> None:
        self._package_path = package_path
        client = importlib.import_module(package_path)
        assert isinstance(client, types.ModuleType)
        self._client = client
        self._document_private_members = bool(document_private_members)
        if member_documenter_classes is None:
            member_documenter_classes = [ClassDocumenter, FunctionDocumenter]
        for _ in member_documenter_classes:
            assert issubclass(_, MemberDocumenter), _
        self._member_documenter_classes = tuple(member_documenter_classes)
        if module_documenters is not None:
            for submodule_documenter in module_documenters:
                assert isinstance(
                    submodule_documenter,
                    ModuleDocumenter,
                    )
            module_documenters = tuple(module_documenters)
        self._module_documenters = module_documenters or ()
        self._member_documenters = self._populate()

    ### SPECIAL METHODS ###

    def __str__(self) -> str:
        result = self._build_preamble()
        result.extend(self._build_toc(self.module_documenters or []))
        for documenter in self._member_documenters:
            result.extend(['', str(documenter)])
        return '\n'.join(result)

    ### PRIVATE METHODS ###

    def _populate(self) -> Sequence[MemberDocumenter]:
        documenters = []
        for name in sorted(dir(self.client)):
            if name.startswith('_') and not self.document_private_members:
                continue
            client = getattr(self.client, name)
            for class_ in self.member_documenter_classes:
                if class_.validate_client(client, self.package_path):
                    path = '{}.{}'.format(client.__module__, client.__name__)
                    documenter = class_(path)
                    documenters.append(documenter)
                    break
        return tuple(documenters)

    ### PRIVATE METHODS ###

    def _build_toc(
        self,
        documenters,
        **kwargs
        ) -> List[str]:
        result = []  # type: List[str]
        if not documenters:
            return result
        result.extend(['', '.. toctree::'])
        result.append('')
        module_documenters = [
            _ for _ in documenters
            if isinstance(_, type(self))
            ]
        for module_documenter in module_documenters:
            path = module_documenter.package_path
            path = path[len(self.package_path) + 1:]
            if module_documenter.is_package:
                path = '{}/index'.format(path)
            result.append('   {}'.format(path))
        return result

    def _build_preamble(self) -> List[str]:
        result = [
            '.. _{}:'.format(self.reference_name),
            '',
            self.package_name,
            '=' * len(self.package_name),
            '',
            '.. automodule:: {}'.format(self.package_path),
            '',
            '.. currentmodule:: {}'.format(self.package_path),
            ]  # type: List[str]
        return result

    ### PUBLIC PROPERTIES ###

    @property
    def client(self) -> object:
        return self._client

    @property
    def is_package(self) -> bool:
        return hasattr(self.client, '__path__')

    @property
    def document_private_members(self) -> bool:
        return self._document_private_members

    @property
    def documentation_path(self) -> pathlib.Path:
        path = pathlib.Path('.').joinpath(*self.package_path.split('.'))
        if self.is_package:
            path = path.joinpath('index')
        return path.with_suffix('.rst')

    @property
    def is_nominative(self) -> bool:
        if self.is_package or len(self.member_documenters) != 1:
            return False
        parts = self.member_documenters[0].package_path.split('.')
        return parts[-1] == parts[-2]

    @property
    def member_documenter_classes(self) -> Sequence[
        Type[MemberDocumenter]]:
        return self._member_documenter_classes

    @property
    def member_documenters(self) -> Sequence[MemberDocumenter]:
        return self._member_documenters

    @property
    def member_documenters_by_section(self) -> Sequence[
        Tuple[str, Sequence[MemberDocumenter]]]:
        result = {}  # type: MutableMapping[str, List[MemberDocumenter]]
        for documenter in self.member_documenters:
            result.setdefault(
                documenter.documentation_section, []).append(documenter)
        return sorted(result.items())

    @property
    def module_documenters(self) -> Sequence['ModuleDocumenter']:
        return self._module_documenters

    @property
    def package_name(self) -> str:
        if '.' in self.package_path:
            return self._package_path.rpartition('.')[-1]
        return self._package_path

    @property
    def package_path(self) -> str:
        return self._package_path

    @property
    def reference_name(self) -> str:
        return self.package_path \
            .replace('_', '-') \
            .replace('.', '--')
