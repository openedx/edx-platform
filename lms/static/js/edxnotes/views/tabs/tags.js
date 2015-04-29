;(function (define, undefined) {
'use strict';
define([
    'gettext', 'jquery', 'underscore', 'js/edxnotes/views/note_group', 'js/edxnotes/views/tab_panel',
    'js/edxnotes/views/tab_view'
], function (gettext, $, _, NoteGroupView, TabPanelView, TabView) {

    var TagsView = TabView.extend({
        scrollToTag: function(tagName) {
            var title;
            if (!this.tabModel.isActive()) {
                this.tabModel.activate();
            }
            title = this.$el.find('.tags-title').filter(function(){ return $(this).text() === tagName.toLowerCase();});
            $('html,body').animate({
                scrollTop: title.offset().top - 10
            },'slow');
        },
        PanelConstructor: TabPanelView.extend({
            id: 'tags-panel',
            title: 'Tags',
            noTags: gettext('no tags'),  // User-defined tags cannot have spaces, so no risk of a collision.

            renderContent: function () {
                var notesByTag = {}, noTags = this.noTags, addNoteForTag, noteInfo, noteList, tags, i,
                    sortedTagNames, container, group;

                // Iterate through all the notes and build up a dictionary structure by tag.
                // Note that the collection will be in most-recently updated order already.

                // The tag structure we are storing is tag: {notes: [], index: <num>}, where
                // index is the collection index when a tag structure is first created. This can be used
                // for tie-breaking when sorting by the total number of notes with a given tag.
                addNoteForTag = function (note, tag, index) {
                    noteInfo = notesByTag[tag.toLowerCase()];
                    if (noteInfo === undefined) {
                        noteInfo = {notes: [], index: index};
                        notesByTag[tag.toLowerCase()] = noteInfo;
                    }
                    noteList = noteInfo.notes;
                    // If a note was tagged with the same tag more than once, don't add again.
                    // We can assume it would be the last element of the list because we iterate through
                    // all tags on a given note before moving on to the text note.
                    if (noteList.length === 0 || noteList[noteList.length -1] !== note) {
                        noteList.push(note);
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

                sortedTagNames = Object.keys(notesByTag).sort(function (a, b) {
                    // "no tags" should always appear last
                    if (a === noTags) {
                        return 1;
                    }
                    else if (b === noTags) {
                        return -1;
                    }
                    else if (notesByTag[a].notes.length > notesByTag[b].notes.length) {
                        return -1;
                    }
                    else if (notesByTag[a].notes.length < notesByTag[b].notes.length) {
                        return 1;
                    }
                    else {
                        // Tie-breaker, go with the list of notes that has the most recently updated note.
                        return notesByTag[a].index - notesByTag[b].index;
                    }
                });

               container = document.createDocumentFragment();

                _.each(sortedTagNames, function (tagName) {
                    group = this.getGroup(tagName);
                    group.addChild(this.getNotes(notesByTag[tagName].notes));
                    container.appendChild(group.render().el);
                }, this);

                this.$el.append(container);
                return this;
            },

            getGroup: function (tagName) {
                var group = new NoteGroupView.GroupView({
                    displayName: tagName,
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
