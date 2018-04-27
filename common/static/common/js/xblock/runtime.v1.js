(function() {
    'use strict';

    this.XBlock.Runtime.v1 = (function() {
        function v1() {
            var block = this;
            this.childMap = function() {
                return v1.prototype.childMap.apply(block, arguments);
            };
            this.children = function() {
                return v1.prototype.children.apply(block, arguments);
            };
        }

        v1.prototype.children = function(block) {
            return $(block).prop('xblock_children');
        };

        v1.prototype.childMap = function(block, childName) {
            var child, idx, len, ref;
            ref = this.children(block);
            for (idx = 0, len = ref.length; idx < len; idx++) {
                child = ref[idx];
                if (child.name === childName) {
                    return child;
                }
            }
            return null;
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
    }());
}).call(this);
