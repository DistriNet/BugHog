<script>
import axios from 'axios'
export default {
    props: {
      eval_params: Object,
    },
    data() {
        return {
            browser_name: null,
            poc: null,
            project: null,
            plot: null,
            revision_source: {
                data: [],
            },
            version_source: {
                data: [],
            },
            revision_range: null,
            x_min: null,
            x_max: null,
            shift_down: false,
        }
    },
    created: function() {
        document.addEventListener("keydown", (e) => {
            if (e.key === "Shift") {
                this.shift_down = true;
            }
        });
        document.addEventListener("keyup", (e) => {
            if (e.key === "Shift") {
                this.shift_down = false;
            }
        });
    },
    methods: {
        init_plot() {
            console.log("Initializing Gantt chart...");

            if (this.revision_source.length === 0 || this.version_source.length === 0) {
                this.x_min = 1;
                this.x_max = 1000000;
            } else {
                this.x_min = Math.min(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                this.x_max = Math.max(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
            }

            this.plot = Bokeh.Plotting.figure({
                title: 'Gantt Chart with Points',
                x_range: [this.x_min, this.x_max],
                y_range: ['Error', 'Not reproduced', 'Reproduced'],
                height: 470,
                width: 900,
                tools: 'xwheel_zoom,pan',
                active_scroll: 'xwheel_zoom'
            });

            if (this.revision_source) {
                this.plot.circle(
                { field: "revision_number" },
                { field: "outcome" },
                6,
                {
                    source: this.revision_source,
                    fill_alpha: 0.8,
                    radius_units: 'screen',
                }
                );
            }

            if (this.version_source) {
                this.plot.rect(
                { field: 'revision_number' },
                { field: 'outcome' },
                12, // width
                12, // height
                {
                    source: this.version_source,
                    color: 'green',
                    angle: 45,
                    fill_alpha: 0.8,
                    width_units: 'screen',
                    height_units: 'screen',
                }
                )

                this.plot.text(
                { field: 'revision_number' },
                { field: 'outcome' },
                { field: 'browser_version_str' },
                {
                    source: this.version_source,
                    x_offset: 0,
                    y_offset: -20,
                    text: { field: 'browser_version_str' },
                    text_color: "black",
                    text_align: 'center',
                    text_font_size: '14px',
                    angle: 45,
                    angle_units: 'deg',
                }
                )
            }

            const urlTemplate = this.browser_name === 'chromium' ? 'https://crrev.com/' :
            this.browser_name === 'firefox' ? 'https://hg.mozilla.org/mozilla-central/rev/' :
            null;

            if (urlTemplate) {
                const tapTool = new Bokeh.TapTool({
                    behavior: 'select',
                    callback: (e) => {
                        var index;
                        if ((index = this.revision_source.selected.indices[0]) !== undefined) {
                            var revision_number = this.revision_source.data.revision_number[index];
                            var browser_version = this.revision_source.data.browser_version[index];
                            var type = "revision";
                        } else if ((index = this.version_source.selected.indices[0]) !== undefined) {
                            var revision_number = this.version_source.data.revision_number[index];
                            var browser_version = this.version_source.data.browser_version[index];
                            var type = "version";
                        } else {
                            console.log("Nothing interesting was selected...");
                            return;
                        }

                        if (this.shift_down === true) {
                            // Ask to remove datapoint
                            this.remove_datapoint(revision_number, browser_version, type);
                        } else {
                            // Open revision page
                            if (this.revision_source.selected.indices.length > 0) {
                                window.open(urlTemplate + revision_number);
                            }
                        }
                        this.revision_source.selected.indices = [];
                        this.version_source.selected.indices = [];
                    }
                });
                this.plot.add_tools(tapTool);
            } else {
                throw new Error(`Unknown browser name: ${browser_name}`);
            }

            this.plot.below[0].formatter = new Bokeh.BasicTickFormatter({ use_scientific: false });

            const hover = new Bokeh.HoverTool({
                tooltips: [
                ['Revision Number', '@revision_number'],
                ['Browser Version', '@browser_version']
                ]
            });
            this.plot.add_tools(hover);

            if (document.getElementById('gantt').childElementCount > 0) {
                document.getElementById('gantt').children[0].remove();
            }
            Bokeh.Plotting.show(this.plot, document.getElementById('gantt'));
            console.log("Gantt chart initialized!");
        },
        update_plot(browser_name, revision_data, version_data, project, poc) {
            if (revision_data === null && version_data === null) {
                return;
            }

            let init_required = this.revision_source === null || this.browser_name !== browser_name;
            this.browser_name = browser_name;
            this.project = project;
            this.poc = poc;

            if (init_required) {
                this.revision_source = new Bokeh.ColumnDataSource({ data: revision_data });;
                this.version_source = new Bokeh.ColumnDataSource({ data: version_data });
                this.init_plot();
            } else {
                this.revision_source.data = revision_data;
                this.version_source.data = version_data;
            }

            this.update_x_range(this.browser_name !== browser_name)
        },
        update_x_range(force_update) {
            console.log("executing update_x_range");
            if (this.plot !== null) {
                if (this.revision_source.length !== 0 || this.version_source.length !== 0) {
                    console.log("calculating new x");
                    var new_x_min = Math.min(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                    var new_x_max = Math.max(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                    if (new_x_min != this.x_min || force_update === true) {
                        console.log("updating x_min");
                        this.x_min = new_x_min;
                        this.plot.x_range.start = new_x_min;
                    }
                    if (new_x_max != this.x_max || force_update === true) {
                        console.log("updating x_max");
                        this.x_max = new_x_max;
                        this.plot.x_range.end = new_x_max;
                    }
                }
            }
        },
        remove_datapoint(revision_number, browser_version, type) {
            console.log("Removing datapoint ", revision_number, type);
            const path = "/api/data/remove/"
            var params = this.eval_params
            params['type'] = type
            params["revision_number"] = revision_number
            params["major_version"] = browser_version
            axios.post(path, params)
            .then((res) => {
            })
            .catch((error) => {
                console.error(error);
            });

        },
    },
};
</script>

<template>
    <div id="gantt"></div>
</template>
