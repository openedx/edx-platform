function KeyboardManager () {
    this.keycode_to_key = {
        9: 'tab',
        27: 'escape',
        13: 'enter',
        190: '.',
        188: ',',
        70: 'f'
    };

    this.handlers = new Object();
    this.help = new Object();

    $(".help").click(_.bind(this.showHelp, this));
}

KeyboardManager.prototype.parseKeybinding = function (keybinding) {
    var parts = keybinding.toLowerCase().split("-");
    var key;
    var shift = false;
    var control = false;
    for (var i = 0; i < parts.length; i++) {
        parts[i] = $.trim(parts[i]);
        if (parts[i] === 'ctrl' || parts[i] === 'control') {
            control = true;
        } else if (parts[i] === 'shift') {
            shift = true;
        } else {
            if (key !== undefined) {
                throw new Error("key is already defined");
            }
            key = parts[i];
        }
    }

    return {
        'key': key,
        'shift': shift,
        'control': control
    };
};

KeyboardManager.prototype.constructKeybinding = function (key, control, shift) {
    if (control && shift) {
        return "control-shift-" + key;
    } else if (control) {
        return "control-" + key;
    } else if (shift) {
        return "shift-" + key;
    } else {
        return key;
    }
};

KeyboardManager.prototype.makeSelectorHandler = function (selector) {
    var that = this;
    return function (e) {
        var keycode = that.keycode_to_key[e.which];
        if (keycode) {
            var handler = that.handlers[selector][that.constructKeybinding(keycode, e.ctrlKey, e.shiftKey)];
            if (handler) {
                handler(e);
            }
        }
    };
}

KeyboardManager.prototype.register = function (properties) {
    if (properties.keybinding === undefined) {
        throw new Error("a keybinding must be provided");
    }

    if (properties.handler === undefined) {
        throw new Error("a handler must be provided");
    }

    if (properties.selector === undefined) {
        properties.selector = "body";
    }

    if (this.handlers[properties.selector] === undefined) {
        this.handlers[properties.selector] = new Object();
        $(properties.selector).on('keydown', this.makeSelectorHandler(properties.selector));
    }

    var keybinding = this.parseKeybinding(properties.keybinding);
    keybinding = this.constructKeybinding(keybinding.key, keybinding.control, keybinding.shift);
    this.handlers[properties.selector][keybinding] = properties.handler;
    this.help[keybinding] = properties.help;
};

KeyboardManager.prototype.showHelp = function () {
    var modal = $("<div/>")
        .addClass("modal")
        .addClass("fade")
        .attr("id", "help-dialog")
        .attr("role", "dialog")

    var dialog = $("<div/>").addClass("modal-dialog");
    modal.append(dialog);

    var content = $("<div/>").addClass("modal-content");
    dialog.append(content);

    var header = $("<div/>").addClass("modal-header");
    content.append(header);
    header.append($("<button/>")
        .addClass("close")
        .attr("data-dismiss", "modal")
        .attr("aria-label", "Close")
        .append($("<span/>")
            .attr("aria-hidden", "true")
            .html("&times;")));
    header.append($("<h4/>")
        .addClass("modal-title")
        .text("Keyboard shortcuts"));

    var body = $("<div/>").addClass("modal-body");
    content.append(body);

    var help_list = $("<div/>").addClass("container-fluid striped");
    body.append(help_list);
    for (var keybinding in this.help) {
        help_list.append($("<div/>")
            .addClass("row")
            .append($("<div/>").addClass("col-md-4 shortcut-key").text(keybinding))
            .append($("<div/>").addClass("col-md-8 shortcut-help").text(this.help[keybinding])));
    }

    var footer = $("<div/>").addClass("modal-footer");
    content.append(footer);
    footer.append($("<button/>")
        .addClass("btn btn-primary")
        .attr("type", "button")
        .attr("data-dismiss", "modal")
        .text("Close"));

    // remove the modal on close
    modal.on("hidden.bs.modal", function () {
        modal.remove();
    });

    $("body").append(modal);
    modal.modal();
};
