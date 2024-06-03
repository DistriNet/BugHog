<script>
export default {
    data() {
        return {
            browser_name: null,
            plot: null,
            revision_source: null,
            version_source: null,
        }
    },
    methods: {
        init_plot() {
            console.log("Initializing Gantt chart...");

            if (this.revision_source.length === 0 && this.version_source.length === 0) {
                var x_min = 1;
                var x_max = 100;
            } else {
                var x_min = Math.min(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                var x_max = Math.max(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
            }

            this.plot = Bokeh.Plotting.figure({
                title: 'Gantt Chart with Points',
                x_range: [x_min, x_max],
                y_range: ['Error', 'Not reproduced', 'Reproduced'],
                height: 470,
                width: 900,
                tools: 'xwheel_zoom,reset,pan',
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
                    callback: () => {
                        if (this.revision_source.selected.indices.length > 0) {
                            let index = this.revision_source.selected.indices[0];
                            let revision_number = this.revision_source.data.revision_number[index];
                            window.open(urlTemplate + revision_number);
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
        update_plot(browser_name, revision_data, version_data) {
            if (revision_data === null && version_data === null) {
                return;
            }

            let init_required = this.revision_source === null || this.browser_name !== browser_name;;
            // let rescale_required = this.browser_name !== browser_name;
            this.browser_name = browser_name;

            if (init_required) {
                this.revision_source = new Bokeh.ColumnDataSource({ data: revision_data });;
                this.version_source = new Bokeh.ColumnDataSource({ data: version_data });
                this.init_plot();
            } else {
                this.revision_source.data = revision_data;
                this.version_source.data = version_data;
            }

            // if (rescale_required) {
            //     this.update_x_range()
            // }
        },
        update_x_range() {
            if (this.plot !== null) {
                if (this.revision_source.length === 0 && this.version_source.length === 0) {
                    var x_min = 1;
                    var x_max = 100;
                } else {
                    var x_min = Math.min(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                    var x_max = Math.max(...this.revision_source.data.revision_number.concat(this.version_source.data.revision_number));
                }
                this.plot.x_range.start = x_min;
                this.plot.x_range.end = x_max;
            }
        },
    },
};
</script>

<template>
    <div id="gantt"></div>
</template>
