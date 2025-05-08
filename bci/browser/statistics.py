def find_biggest_unavailability_gap():
    revision_nb_mapping = REVISION_NUMBER_MAPPING

    revision_nbs = [int(rev) for rev in revision_nb_mapping.keys()]
    revision_nbs.sort()
    # Find the biggest gap between two revision numbers
    biggest_gap = 0
    biggest_gap_start = None
    biggest_gap_end = None
    for i in range(1, len(revision_nbs)):
        start = revision_nbs[i - 1]
        end = revision_nbs[i]
        gap = end - start
        print(f'{i}: {start} - {end} = {gap}')
        if gap > biggest_gap:
            biggest_gap = gap
            biggest_gap_start = start
            biggest_gap_end = end

    print(f"The biggest gap is between revision numbers {biggest_gap_start} and {biggest_gap_end} with a gap of {biggest_gap}")


def get_nb_of_revisions_per_major_version():
    binary_availability = BINARY_AVAILABILITY_MAPPING

    major_versions = {}
    for item in binary_availability.values():
        major_version = item['app_version']
        if major_version not in major_versions:
            major_versions[major_version] = {item['revision_number']}
        major_versions[major_version].add(item['revision_number'])

    for major_version, nb_of_revisions in major_versions.items():
        print(f'Major version {major_version}: {len(nb_of_revisions)} revisions (%)')


if __name__ == '__main__':
    find_biggest_unavailability_gap()
    get_nb_of_revisions_per_major_version()
