from uqbar.apis.ModuleDocumenter import ModuleDocumenter
from uqbar.apis.RootDocumenter import RootDocumenter


class SummarizingRootDocumenter(RootDocumenter):
    """
    A summarizing root documenter.

    Like the :py:class:`~uqbar.apis.SummarizingClassDocumenter` and
    :py:class:`~uqbar.apis.SummarizingModuleDocumenter`, this subclass of
    :py:class:`~uqbar.apis.RootDocumenter` generates root API documentation
    with additional information and organization.

    Each visited module or package receives its own section with members
    organized by their documentation sections and listed in autosummary tables.

    ::

        >>> import uqbar.apis
        >>> documenter = uqbar.apis.SummarizingRootDocumenter(
        ...     module_documenters=[
        ...         uqbar.apis.ModuleDocumenter('uqbar.io'),
        ...         uqbar.apis.ModuleDocumenter('uqbar.strings'),
        ...         ],
        ...     )
        >>> print(str(documenter))
        API
        ===
        <BLANKLINE>
        .. toctree::
           :hidden:
        <BLANKLINE>
           uqbar/io/index
           uqbar/strings
        <BLANKLINE>
        .. raw:: html
        <BLANKLINE>
           <hr/>
        <BLANKLINE>
        .. rubric:: :ref:`uqbar.io <uqbar--io>`
           :class: section-header
        <BLANKLINE>
        -  Functions
        <BLANKLINE>
           .. autosummary::
              :nosignatures:
        <BLANKLINE>
              ~uqbar.io.find_common_prefix
              ~uqbar.io.relative_to
              ~uqbar.io.walk
              ~uqbar.io.write
        <BLANKLINE>
        .. raw:: html
        <BLANKLINE>
           <hr/>
        <BLANKLINE>
        .. rubric:: :ref:`uqbar.strings <uqbar--strings>`
           :class: section-header
        <BLANKLINE>
        -  Functions
        <BLANKLINE>
           .. autosummary::
              :nosignatures:
        <BLANKLINE>
              ~uqbar.strings.delimit_words
              ~uqbar.strings.normalize
              ~uqbar.strings.to_dash_case
              ~uqbar.strings.to_snake_case

    :param module_documenters: a list of of documenters for modules and
        packages of the root documenter; these are generated by an
        :py:class:`~uqbar.apis.APIBuilder` instance rather than the module
        documenter directly
    """

    def __str__(self):
        result = [
            self.title,
            '=' * len(self.title),
            '',
            '.. toctree::',
            '   :hidden:',
            '',
            ]
        for documenter in self.module_documenters:
            path = documenter.package_path.replace('.', '/')
            if documenter.is_package:
                path += '/index'
            result.append('   {}'.format(path))
        for module_documenter, documenters_by_section in self._recurse(self):
            result.extend([
                '',
                '.. raw:: html',
                '',
                '   <hr/>',
                '',
                '.. rubric:: :ref:`{} <{}>`'.format(
                    module_documenter.package_path,
                    module_documenter.reference_name,
                    ),
                '   :class: section-header',
                ])
            for section_name, documenters in documenters_by_section:
                result.extend([
                    '',
                    '-  {}'.format(section_name),
                    '',
                    '   .. autosummary::',
                    '      :nosignatures:',
                    '',
                    ])
                for documenter in documenters:
                    result.append('      ~{}'.format(documenter.package_path))
        return '\n'.join(result)

    def _recurse(self, documenter):
        result = []
        if (
            isinstance(documenter, ModuleDocumenter) and
            not documenter.is_nominative
            ):
            result.append((
                documenter,
                documenter.member_documenters_by_section,
                ))
        for module_documenter in documenter.module_documenters:
            result.extend(self._recurse(module_documenter))
        return result