from . import XMLStore
from ttk2.formats import Unit
from xml.etree import ElementTree


class XLIFFStore(XMLStore):

    GLOB = [".xlf"]
    VERSION = "1.2"

    def read(self, file_, lang, srclang):
        xml_file = ElementTree.parse(file_)

        def validate_language(element, base_language):
            """
            Retrieves language information from the given ``element``,
            validating it against the given ``base_language``.

            If for any reason the ``base_language`` does not exist but
            retrieved language is available, this one is returned as the valid
            language.
            """
            element_lang = element.get(
                "{http://www.w3.org/XML/1998/namespace}lang"
            )
            if base_language is None:
                return element_lang

            elif element_lang is not None and element_lang != base_language:
                raise ValueError(
                    "Element language ({}) must be the same "
                    "defined at file element ({}).".format(
                        element_lang,
                        base_language,
                    )
                )

            return base_language

        root_element = xml_file.getroot()
        for file_element in root_element.findall("file"):
            source_lang = file_element.get("source-language")
            target_lang = file_element.get("target-language")

            body_element = file_element.find("body")
            if body_element is None:
                continue

            source_units = []
            target_units = []
            for unit_element in body_element.findall("trans-unit"):

                # Source unit
                source_element = unit_element.find("source")
                if source_element is None:
                    raise RuntimeError(
                        "Missing source text, which is mandatory!"
                    )

                # Source unit may be ignored when given an invalid ``srclang``.
                source_text = source_element.text
                if srclang is not None and srclang.strip():
                    source_lang = validate_language(
                        source_element,
                        source_lang,
                    )
                    source_units.append(Unit(source_text, source_text))

                # Target unit
                target_element = unit_element.find("target")
                if target_element is None:
                    continue

                target_lang = validate_language(target_element, target_lang)
                target_units.append(Unit(source_text, target_element.text))

            # Post processing necessary to apply the updated source and target
            # languages to the created units.
            def update_language(units, language):
                for unit in units:
                    unit.lang = language

            update_language(source_units, source_lang or srclang)
            update_language(target_units, target_lang or lang)

            # Now it is time to persist all these information.
            self.units.extend(source_units)
            self.units.extend(target_units)

    def serialize(self):
        """
        Serialization will create an output with XLIFF contents, following the
        specifications given at `OASIS`_ website.

        .. _`OASIS`: http://docs.oasis-open.org/xliff/v1.2/os/xliff-core.html
        """
        if len(self.units) <= 0:
            raise RuntimeError(
                "It is necessary at least one unit to create a XLIFF content."
            )

        root_element = ElementTree.Element("xliff", {"version": self.VERSION})

        # TODO: as XLIFF allows the addition of multiple "file" elements it is
        #       necessary to define if this code will support it and then group
        #       units by the filename.

        # According to OASIS documentation both source and target language must
        # be defined here at "file" element.
        file_element = self._element("file", root_element)

        # TODO: There is no way for defining the languages without violating
        #       the current API. It is necessary to discuss some ideas before
        #       any changes. Even that the :class:`.Unit` has a reference to a
        #       ``lang`` attribute, which I understand is related to the target
        #       language, XLIFF is driven by the information set to the "file"
        #       element. Even with optional attribute "xml:lang" for both
        #       source and target they must match their respective attributes
        #       defined at "file" element.
        file_element.attrib["source-language"] = "en"
        file_element.attrib["target-language"] = "todo"

        # Now let's get all units.
        body_element = self._element("body", file_element)
        for index, unit in enumerate(self.units):
            unit_element = self._element("trans-unit", body_element)
            unit_element.attrib["id"] = str(index)
            self._element("source", unit_element, unit.key)

            # Target is optional.
            value = unit.value
            if value is not None and value.strip():
                self._element("target", unit_element, value)

        return self._pretty_print(ElementTree.tostring(root_element))
