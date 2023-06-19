from bci.evaluations.xsleaks.testcase.testcase import TestCase


class Case01(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case1/main/")
        report = self.read_report("case1.json")
        return report


class Case02(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case2/main/")
        report = self.read_report("case2.json")
        return report


class Case03(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case3/main/")
        report = self.read_report("case3.json")
        return report


class Case04(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case4/main/", sleep_after_visit=15)
        report = self.read_report("case4.json")
        return report


class Case05(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case5/main/")
        report = self.read_report("case5.json")
        return report


class Case06(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case6/a/", sleep_after_visit=20)
        report = self.read_report("case6.json")
        return report


class Case07(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case7/main/")
        report = self.read_report("case7.json")
        return report


class Case08(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case8/main/")
        report = self.read_report("case8.json")
        return report


class Case09(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case9/main/")
        report = self.read_report("case9.json")
        return report


class Case10(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case10/main/")
        report = self.read_report("case10.json")
        return report


class Case11(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case11/redirect/")
        self.visit("https://attack.er/custom/case11/no_redirect/")
        report1 = self.read_report("case11_redirect.json")
        report2 = self.read_report("case11_no_redirect.json")

        if report1 and report2:
            report = {**report1, **report2}
        elif report1:
            report = report1
            report["no_redirect"] = None
        else:
            report = report2
            report["redirect"] = None
        report["xsleak_reproduced"] = report["no_redirect"] and report["redirect"]
        return report


class Case12(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case12/main/")
        report = self.read_report("case12.json")
        return report


class Case13(TestCase):

    def run(self):
        self.visit("https://sub.leak.test/resource1")
        self.visit("https://attack.er/custom/case13/main/", clean_profile=False)
        report = self.read_report("case13.json")
        return report


class Case15(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case15/main/")
        report = self.read_report("case15.json")
        return report


class Case18(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case18/main/")
        report = self.read_report("case18.json")
        return report


class Case19(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case19/main/")
        report = self.read_report("case19.json")
        return report


class Case20(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case20/main/")
        report = self.read_report("case20.json")
        return report


class Case25(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case25/main/")
        report = self.read_report("case25.json")
        return report


class Case25b(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case25/old/")
        report = self.read_report("case25b.json")
        return report


class Case29(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case29/main/")
        report = self.read_report("case29.json")
        return report


class Case30(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case30/main/")
        report = self.read_report("case30.json")
        return report


class Case31(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/case31/main/")
        report = self.read_report("case31.json")
        return report


class DefaultSameSite(TestCase):

    def run(self):
        self.visit("https://re.port/set_cookie/generic_cookie/1/")
        self.visit("https://attack.er/custom/default_samesite/main", clean_profile=False)
        report = self.read_report("default_samesite.json")
        return report


class SameSite(TestCase):

    def run(self):
        self.visit("https://re.port/set_lax_cookie/ss_lax_cookie/1/")
        self.visit("https://attack.er/custom/samesite/main", clean_profile=False)
        report = self.read_report("samesite.json")
        return report


class SecFetchSite(TestCase):

    def run(self):
        self.visit("https://attack.er/custom/SecFetchSite/main")
        report = self.read_report("SecFetchSite.json")
        return report


class NetworkIsolation(TestCase):

    def run(self):
        self.visit("https://leak.test/custom/NetworkIsolation/main")
        self.visit("https://attack.er/custom/NetworkIsolation/main", clean_profile=False)
        report = self.read_report("NetworkIsolation.json")
        return report
