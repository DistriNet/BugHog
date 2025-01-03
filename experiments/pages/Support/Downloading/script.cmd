# Download file short-text.txt with content 123456789
NAVIGATE https://a.test/Support/Downloading/main

SLEEP 1

# These commands would stop the evaluation and not report a leak
# ASSERT_FILE_CONTAINS i-dont-exist.txt 234
# ASSERT_FILE_CONTAINS short-text.txt i-am-not-in-the-file

# This command will continue the evaluation and report a leak
ASSERT_FILE_CONTAINS short-text.txt 234

REPORT_LEAK