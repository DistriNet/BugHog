
def get_all_cli_options():
    return list(cli_options.keys())


def get_associated_arguments(cli_option):
    if cli_option not in cli_options.keys():
        raise AttributeError("Could not find cli option '%s'" % cli_option)
    return cli_options[cli_option].split(" ")


cli_options = {
}
