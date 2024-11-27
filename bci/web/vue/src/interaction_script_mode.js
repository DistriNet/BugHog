const KEYWORDS = "NAVIGATE|CLICK_POSITION|CLICK|WRITE|PRESS|HOLD|RELEASE|HOTKEY|SLEEP|SCREENSHOT|REPORT_LEAK";

ace.define("ace/mode/interaction_script_highlight_rules",["require","exports","module","ace/lib/oop","ace/mode/text_highlight_rules"], function(require, exports, module){"use strict";
    const oop = require("../lib/oop");
    const TextHighlightRules = require("./text_highlight_rules").TextHighlightRules;

    const HighlightRules = function() {

        var keywordMapper = this.createKeywordMapper({
            "keyword": KEYWORDS,
        }, "argument", true);

        this.$rules = {
            "start" : [ {
                token : "comment",
                regex : "#.*$"
            }, {
                token : "constant.numeric", // float
                regex : "[+-]?\\d+(?:(?:\\.\\d*)?(?:[eE][+-]?\\d+)?)?\\b"
            }, {
                token : keywordMapper,
                regex : "[a-zA-Z_$][a-zA-Z0-9_$]*\\b"
            } ]
        };
        this.normalizeRules();
    };

    oop.inherits(HighlightRules, TextHighlightRules);
    exports.HighlightRules = HighlightRules;
});

ace.define("ace/mode/interaction_script",["require","exports","module","ace/lib/oop","ace/mode/text", "ace/mode/interaction_script_highlight_rules"], function(require, exports){"use strict";
    const oop = require("ace/lib/oop");
    const TextMode = require("ace/mode/text").Mode;
    const HighlightRules = require("ace/mode/interaction_script_highlight_rules").HighlightRules;
    const Mode = function() {
        this.HighlightRules = HighlightRules;
    };
    oop.inherits(Mode, TextMode);
    exports.Mode = Mode;
});

const getMode = () => new Promise((resolve) => ace.require(["ace/mode/interaction_script"], resolve));

export {
    getMode,
};