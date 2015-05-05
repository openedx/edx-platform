;(function (define, undefined) {
'use strict';
define([
    'gettext', 'underscore', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
    'js/edxnotes/views/tab_view'
], function (gettext, _, NoteGroupView, TabPanelView, TabView) {
    var TagsView = TabView.extend({
        PanelConstructor: TabPanelView.extend({
            id: 'tags-panel',
            title: 'Tags',
            noTags: gettext('no tags'),  // User-defined tags cannot have spaces, so no risk of a collision.

            renderContent: function () {
                var notes_by_tag = {}, noTags = this.noTags, addNoteForTag, note_info, note_list, tags, i,
                    sorted_tag_names, container, group;

                // Iterate through all the notes and build up a dictionary structure by tag.
                // Note that the collection will be in most-recently updated order already.

                // The tag structure we are storing is tag: {notes: [], index: <num> }, where
                // index is the collection index when a tag structure is first created. This can be used
                // for tie-breaking when sorting by the total number of notes with a given tag.
                addNoteForTag = function (note, tag, index) {
                    note_info = notes_by_tag[tag.toLowerCase()];
                    if (note_info === undefined) {
                        note_info = {notes: [], index: index};
                        notes_by_tag[tag.toLowerCase()] = note_info;
                    }
                    note_list = note_info.notes;
                    // If a note was tagged with the same tag more than once, don't add again.
                    // We can assume it would be the last element of the list because we iterate through
                    // all tags on a given note before moving on to the text note.
                    if (note_list.length === 0 || note_list[note_list.length -1] !== note) {
                        note_list.push(note);
                    }
                };

                this.collection.each(function(note, index){
                    tags = note.get('tags');
                    if (tags.length === 0) {
                        addNoteForTag(note, noTags, index);
                    }
                    else {
                        for (i = 0; i < tags.length; i++) {
                            addNoteForTag(note, tags[i], index);
                        }
                    }
                });

                sorted_tag_names = Object.keys(notes_by_tag).sort(function (a, b) {
                    // "no tags" should always appear last
                    if (a === noTags) {
                        return 1;
                    }
                    else if (b === noTags) {
                        return -1;
                    }
                    else if (notes_by_tag[a].notes.length > notes_by_tag[b].notes.length) {
                        return -1;
                    }
                    else if (notes_by_tag[a].notes.length < notes_by_tag[b].notes.length) {
                        return 1;
                    }
                    else {
                        // Tie-breaker, go with the list of notes that has the most recently updated note.
                        return notes_by_tag[a].index - notes_by_tag[b].index;
                    }
                });

               container = document.createDocumentFragment();

                _.each(sorted_tag_names, function (tag_name) {
                    group = this.getGroup(tag_name);
                    group.addChild(this.getNotes(notes_by_tag[tag_name].notes));
                    container.appendChild(group.render().el);
                }, this);

                this.$el.append(container);
                return this;
            },

            getGroup: function (tag_name) {
                var group = new NoteGroupView.groupView({
                    displayName: tag_name,
                    template: '<h3 class="tags-title"><%- displayName %></h3>',
                    className: "note-group"
                });
                this.children.push(group);
                return group;
            }
        }),

        tabInfo: {
            name: gettext('Tags'),
            identifier: 'view-tags',
            icon: 'fa fa-tag'
        }
    });

    return TagsView;
});
}).call(this, define || RequireJS.define);