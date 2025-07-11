from bughog.subject.subject import Subject


class V8Subject(Subject):

    @property
    def name(self) -> str:
        return 'v8'

    @staticmethod
    def get_availability() -> dict:
        """
        Returns availability data (minimum and maximu, release versions, and configuration options) of the subject.
        """
        return {
            'name': 'v8',
            'min_version': 1,
            'max_version': self.get_most_recent_major_release_version()
        }
