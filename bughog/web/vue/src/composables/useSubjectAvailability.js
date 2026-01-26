import axios from 'axios';
import { ref } from 'vue';

export function useSubjectAvailability(post_init_callback) {

    const subject_availability_dict = ref([]);

    const subject_availability = {
        fetch_subject_availability() {
        const path = `/api/subject/`;
        axios.get(path)
            .then((res) => {
                if (res.data.status == "OK") {
                    subject_availability_dict.value = res.data.subject_availability;
                    if (post_init_callback === undefined || post_init_callback === null) {
                        console.warn("useSubjectAvailability did not receive a post_init_callback function.")
                    } else {
                        post_init_callback();
                    }
                }
            })
            .catch((error) => {
                console.error(error);
            });
        },

        is_empty() {
            return subject_availability_dict.value.length === 0;
        },

        get_available_subject_types() {
            return subject_availability_dict.value.map(entry => entry.subject_type).sort();
        },

        get_available_subjects_for_type(subject_type) {
            if (subject_availability_dict.value.length == 0 || subject_type === null) {
                return [];
            } else {
                const result = subject_availability_dict.value.find(type_entry => type_entry.subject_type === subject_type);
                return result === undefined ? [] : result.subjects;
            }
        },

        get_available_subject_names_for_type(subject_type) {
            const subjects = this.get_available_subjects_for_type(subject_type);
            return subjects.map(subject => subject.name);
        },

        get_subject_by_name(subject_type, subject_name) {
            if (this.is_empty() || subject_type === null || subject_name === null) {
                return null;
            } else {
                const subject = this.get_available_subjects_for_type(subject_type).find(subject => subject.name === subject_name);
                return subject === undefined ? null : subject;
            }
        },

        get_subject_version_range(subject_type, subject_name) {
            if (this.is_empty() || subject_type === null || subject_name === null) {
                return [-1, -1];
            } else {
                const subject = this.get_subject_by_name(subject_type, subject_name);
                return subject === null ? [-1, -1] : [subject.min_version, subject.max_version];
            }
        }
    }

    subject_availability.fetch_subject_availability();
    console.log("Subject availability has been initialized.")

  return {
    subject_availability,
  }
}
