from bci.evaluations.xsleaks.testcase.testcase import TestCase


class First(TestCase):

    def run(self):
        self.visit("https://leak.test/custom/test/main")
        self.visit("https://leak.test/custom/test/main")
        self.visit("https://leak.test/custom/test/main")
        self.visit("https://leak.test/custom/test/main")
        self.visit("https://leak.test/custom/test/main")
        report = self.read_report("test.json")
        return report
