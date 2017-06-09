(function() {
    'use strict';

    XBlock.Runtime.v1 = (function() {
        function v1() {
            var _this = this;
            this.childMap = function() {
                return v1.prototype.childMap.apply(_this, arguments);
            };
            this.children = function() {
                return v1.prototype.children.apply(_this, arguments);
            };
        }

        v1.prototype.children = function(block) {
            return $(block).prop('xblock_children');
        };

        v1.prototype.childMap = function(block, childName) {
            var child, _i, _len, _ref;
            _ref = this.children(block);
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                child = _ref[_i];
                if (child.name === childName) {
                    return child;
                }
            }
        };

        /**
         * Notify the client-side runtime that an event has occurred.
         *
         * This allows the runtime to update the UI in a consistent way
         * for different XBlocks.
         * `name` is an arbitrary string (for example, "save")
         * `data` is an object (for example, {state: 'starting'})
         * The default implementation is a no-op.
         *
         * WARNING: This is an interim solution and not officially supported!
         */
        v1.prototype.notify = function() {
            // Do nothing
        };

        return v1;
    })();
}).call(this);
