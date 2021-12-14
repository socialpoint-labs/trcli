from pathlib import Path
from typing import Union
from junitparser import TestCase, TestSuite, JUnitXml, Attr, JUnitXmlError
from xml.etree import ElementTree as etree
from trcli.readers.file_parser import FileParser
from trcli.data_classes.dataclass_testrail import (
    TestRailCase,
    TestRailSuite,
    TestRailSection,
    TestRailProperty,
    TestRailResult,
)

TestCase.id = Attr("id")
TestSuite.id = Attr("id")
JUnitXml.id = Attr("id")


class JunitParser(FileParser):
    @classmethod
    def _add_root_element_to_tree(cls, filepath: Union[str, Path]) -> etree:
        """
        Because some of junits have XML root as testsuites and some not.
        This way make sure that we always have testsuites root.
        """
        tree = etree.parse(filepath)
        root_elem = tree.getroot()
        if root_elem.tag == "testsuites":
            return tree
        elif root_elem.tag == "testsuite":
            new_root = etree.Element("testsuites")
            new_root.insert(0, root_elem)
            return etree.ElementTree(new_root)
        else:
            raise JUnitXmlError("Invalid format.")

    def parse_file(self) -> TestRailSuite:
        suite = JUnitXml.fromfile(
            self.filepath, parse_func=self._add_root_element_to_tree
        )

        test_sections = []
        for section in suite:
            test_cases = []
            properties = []
            for prop in section.properties():
                properties.append(TestRailProperty(prop.name, prop.value))
            for case in section:

                test_cases.append(
                    TestRailCase(
                        section.id,
                        case.name,
                        case.id,
                        case.time,
                        result=(
                            TestRailResult(case.id, junit_result_unparsed=case.result)
                        ),
                    )
                )
            test_sections.append(
                TestRailSection(
                    section.name,
                    suite.id,
                    time=section.time,
                    section_id=section.id,
                    testcases=test_cases,
                    properties=properties,
                )
            )

        suite = TestRailSuite(
            suite.name, suite_id=suite.id, time=suite.time, testsections=test_sections
        )
        return suite
