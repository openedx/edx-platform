/* globals $$course_id, Content, Markdown, URI */
(function() {
    'use strict';
    this.DiscussionUtil = (function() {

        function DiscussionUtil() {
        }

        DiscussionUtil.wmdEditors = {};

        DiscussionUtil.getTemplate = function(id) {
            return $("script#" + id).html();
        };

        DiscussionUtil.setUser = function(user) {
            this.user = user;
        };

        DiscussionUtil.getUser = function() {
            return this.user;
        };

        DiscussionUtil.loadRoles = function(roles) {
            this.roleIds = roles;
        };

        DiscussionUtil.isStaff = function(userId) {
            var staff;
            if (_.isUndefined(userId)) {
                userId = this.user ? this.user.id : void 0;
            }
            staff = _.union(this.roleIds.Moderator, this.roleIds.Administrator);
            return _.include(staff, parseInt(userId));
        };

        DiscussionUtil.isTA = function(userId) {
            var ta;
            if (_.isUndefined(userId)) {
                userId = this.user ? this.user.id : void 0;
            }
            ta = _.union(this.roleIds['Community TA']);
            return _.include(ta, parseInt(userId));
        };

        DiscussionUtil.isPrivilegedUser = function(userId) {
            return this.isStaff(userId) || this.isTA(userId);
        };

        DiscussionUtil.bulkUpdateContentInfo = function(infos) {
            var id, info, _results;
            _results = [];
            for (id in infos) {
                if (infos.hasOwnProperty(id)) {
                    info = infos[id];
                    _results.push(Content.getContent(id).updateInfo(info));
                }
            }
            return _results;
        };

        DiscussionUtil.generateDiscussionLink = function(cls, txt, handler) {
            return $("<a>")
                .addClass("discussion-link").attr("href", "#")
                .addClass(cls).html(txt).click(function() {return handler(this);});
        };

        DiscussionUtil.urlFor = function(name, param, param1, param2) {
            return {
                follow_discussion: "/courses/" + $$course_id + "/discussion/" + param + "/follow",
                unfollow_discussion: "/courses/" + $$course_id + "/discussion/" + param + "/unfollow",
                create_thread: "/courses/" + $$course_id + "/discussion/" + param + "/threads/create",
                update_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/update",
                create_comment: "/courses/" + $$course_id + "/discussion/threads/" + param + "/reply",
                delete_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/delete",
                flagAbuse_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/flagAbuse",
                unFlagAbuse_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/unFlagAbuse",
                flagAbuse_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/flagAbuse",
                unFlagAbuse_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/unFlagAbuse",
                upvote_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/upvote",
                downvote_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/downvote",
                pin_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/pin",
                un_pin_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/unpin",
                undo_vote_for_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/unvote",
                follow_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/follow",
                unfollow_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/unfollow",
                update_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/update",
                endorse_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/endorse",
                create_sub_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/reply",
                delete_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/delete",
                upvote_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/upvote",
                downvote_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/downvote",
                undo_vote_for_comment: "/courses/" + $$course_id + "/discussion/comments/" + param + "/unvote",
                upload: "/courses/" + $$course_id + "/discussion/upload",
                users: "/courses/" + $$course_id + "/discussion/users",
                search: "/courses/" + $$course_id + "/discussion/forum/search",
                retrieve_discussion: "/courses/" + $$course_id + "/discussion/forum/" + param + "/inline",
                retrieve_single_thread: "/courses/" + $$course_id + "/discussion/forum/" + param + "/threads/" + param1,
                openclose_thread: "/courses/" + $$course_id + "/discussion/threads/" + param + "/close",
                permanent_link_thread: "/courses/" + $$course_id + "/discussion/forum/" + param + "/threads/" + param1,
                permanent_link_comment: "/courses/" + $$course_id +
                                        "/discussion/forum/" + param + "/threads/" + param1 + "#" + param2,
                user_profile: "/courses/" + $$course_id + "/discussion/forum/users/" + param,
                followed_threads: "/courses/" + $$course_id + "/discussion/forum/users/" + param + "/followed",
                threads: "/courses/" + $$course_id + "/discussion/forum",
                "enable_notifications": "/notification_prefs/enable/",
                "disable_notifications": "/notification_prefs/disable/",
                "notifications_status": "/notification_prefs/status/"
            }[name];
        };

        DiscussionUtil.ignoreEnterKey = function(event) {
            if (event.which === 13) {
                return event.preventDefault();
            }
        };

        DiscussionUtil.activateOnSpace = function(event, func) {
            if (event.which === 32) {
                event.preventDefault();
                return func(event);
            }
        };

        DiscussionUtil.makeFocusTrap = function(elem) {
            return elem.keydown(function(event) {
                if (event.which === 9) {
                    return event.preventDefault();
                }
            });
        };

        DiscussionUtil.showLoadingIndicator = function(element, takeFocus) {
            this.$_loading = $(
                "<div class='loading-animation' tabindex='0'><span class='sr'>" +
                gettext("Loading content") +
                "</span></div>"
            );
            element.after(this.$_loading);
            if (takeFocus) {
                this.makeFocusTrap(this.$_loading);
                return this.$_loading.focus();
            }
        };

        DiscussionUtil.hideLoadingIndicator = function() {
            return this.$_loading.remove();
        };

        DiscussionUtil.discussionAlert = function(header, body) {
            var alertDiv, alertTrigger;
            if ($("#discussion-alert").length === 0) {
                alertDiv = $(
                    "<div class='modal' role='alertdialog' id='discussion-alert' " +
                    "aria-describedby='discussion-alert-message'/>"
                ).css("display", "none");
                alertDiv.html(
                    "<div class='inner-wrapper discussion-alert-wrapper'>" +
                    "   <button class='close-modal dismiss' title='" + gettext("Close") + "'>" +
                    "       <span class='icon fa fa-times' aria-hidden='true'></span>" +
                    "   </button>" +
                    "   <header><h2/><hr/></header>" +
                    "   <p id='discussion-alert-message'/><hr/>" +
                    "   <button class='dismiss'>" + gettext("OK") + "</button>" +
                    "</div>"
                );
                this.makeFocusTrap(alertDiv.find("button"));
                alertTrigger = $("<a href='#discussion-alert' id='discussion-alert-trigger'/>").css("display", "none");
                alertTrigger.leanModal({
                    closeButton: "#discussion-alert .dismiss",
                    overlay: 1,
                    top: 200
                });
                $("body").append(alertDiv).append(alertTrigger);
            }
            $("#discussion-alert header h2").html(header);
            $("#discussion-alert p").html(body);
            $("#discussion-alert-trigger").click();
            return $("#discussion-alert button").focus();
        };

        DiscussionUtil.safeAjax = function(params) {
            var $elem, deferred, request,
                self = this;
            $elem = params.$elem;
            if ($elem && $elem.attr("disabled")) {
                deferred = $.Deferred();
                deferred.reject();
                return deferred.promise();
            }
            params.url = URI(params.url).addSearch({
                ajax: 1
            });
            params.beforeSend = function() {
                if ($elem) {
                    $elem.attr("disabled", "disabled");
                }
                if (params.$loading) {
                    if (params.loadingCallback) {
                        return params.loadingCallback.apply(params.$loading);
                    } else {
                        return self.showLoadingIndicator($(params.$loading), params.takeFocus);
                    }
                }
            };
            if (!params.error) {
                params.error = function() {
                    self.discussionAlert(
                        gettext("Sorry"),
                        gettext(
                            "We had some trouble processing your request. Please ensure you have copied any " +
                            "unsaved work and then reload the page.")
                    );
                };
            }
            request = $.ajax(params).always(function() {
                if ($elem) {
                    $elem.removeAttr("disabled");
                }
                if (params.$loading) {
                    if (params.loadedCallback) {
                        return params.loadedCallback.apply(params.$loading);
                    } else {
                        return self.hideLoadingIndicator();
                    }
                }
            });
            return request;
        };

        DiscussionUtil.updateWithUndo = function(model, updates, safeAjaxParams, errorMsg) {
            var undo,
                self = this;
            if (errorMsg) {
                safeAjaxParams.error = function() {
                    return self.discussionAlert(gettext("Sorry"), errorMsg);
                };
            }
            undo = _.pick(model.attributes, _.keys(updates));
            model.set(updates);
            return this.safeAjax(safeAjaxParams).fail(function() {
                return model.set(undo);
            });
        };

        DiscussionUtil.bindLocalEvents = function($local, eventsHandler) {
            var event, eventSelector, handler, selector, _ref, _results;
            _results = [];
            for (eventSelector in eventsHandler) {
                if (eventsHandler.hasOwnProperty(eventSelector)){
                    handler = eventsHandler[eventSelector];
                    _ref = eventSelector.split(' ');
                    event = _ref[0];
                    selector = _ref[1];
                    _results.push($local(selector).unbind(event)[event](handler));
                }
            }
            return _results;
        };

        DiscussionUtil.formErrorHandler = function(errorsField) {
            return function(xhr, textStatus, error) {
                var makeErrorElem, response, _i, _len, _ref, _results;
                makeErrorElem = function(message) {
                    return $("<li>").addClass("post-error").html(message);
                };
                errorsField.empty().show();
                if (xhr.status === 400) {
                    response = JSON.parse(xhr.responseText);
                    if (response.errors) {
                        _ref = response.errors;
                        _results = [];
                        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                            error = _ref[_i];
                            _results.push(errorsField.append(makeErrorElem(error)));
                        }
                        return _results;
                    }
                } else {
                    return errorsField.append(makeErrorElem(
                        gettext("We had some trouble processing your request. Please try again."))
                    );
                }
            };
        };

        DiscussionUtil.clearFormErrors = function(errorsField) {
            return errorsField.empty();
        };

        DiscussionUtil.postMathJaxProcessor = function(text) {
            var RE_DISPLAYMATH, RE_INLINEMATH;
            RE_INLINEMATH = /^\$([^\$]*)\$/g;
            RE_DISPLAYMATH = /^\$\$([^\$]*)\$\$/g;
            return this.processEachMathAndCode(text, function(s, type) {
                if (type === 'display') {
                    return s.replace(RE_DISPLAYMATH, function($0, $1) {
                        return "\\[" + $1 + "\\]";
                    });
                } else if (type === 'inline') {
                    return s.replace(RE_INLINEMATH, function($0, $1) {
                        return "\\(" + $1 + "\\)";
                    });
                } else {
                    return s;
                }
            });
        };

        DiscussionUtil.makeWmdEditor = function($content, $local, cls_identifier) {
            var appended_id, editor, elem, id, imageUploadUrl, placeholder, _processor;
            elem = $local("." + cls_identifier);
            placeholder = elem.data('placeholder');
            id = elem.attr("data-id");
            appended_id = "-" + cls_identifier + "-" + id;
            imageUploadUrl = this.urlFor('upload');
            _processor = function(self) {
                return function(text) {
                    return self.postMathJaxProcessor(text);
                };
            };
            editor = Markdown.makeWmdEditor(elem, appended_id, imageUploadUrl, _processor(this));
            this.wmdEditors["" + cls_identifier + "-" + id] = editor;
            if (placeholder) {
                elem.find("#wmd-input" + appended_id).attr('placeholder', placeholder);
            }
            return editor;
        };

        DiscussionUtil.getWmdEditor = function($content, $local, cls_identifier) {
            var elem, id;
            elem = $local("." + cls_identifier);
            id = elem.attr("data-id");
            return this.wmdEditors["" + cls_identifier + "-" + id];
        };

        DiscussionUtil.getWmdInput = function($content, $local, cls_identifier) {
            var elem, id;
            elem = $local("." + cls_identifier);
            id = elem.attr("data-id");
            return $local("#wmd-input-" + cls_identifier + "-" + id);
        };

        DiscussionUtil.getWmdContent = function($content, $local, cls_identifier) {
            return this.getWmdInput($content, $local, cls_identifier).val();
        };

        DiscussionUtil.setWmdContent = function($content, $local, cls_identifier, text) {
            this.getWmdInput($content, $local, cls_identifier).val(text);
            return this.getWmdEditor($content, $local, cls_identifier).refreshPreview();
        };

        DiscussionUtil.processEachMathAndCode = function(text, processor) {
            var $div, ESCAPED_BACKSLASH, ESCAPED_DOLLAR, RE_DISPLAYMATH, RE_INLINEMATH, cnt, codeArchive, processedText;
            codeArchive = [];
            RE_DISPLAYMATH = /^([^\$]*?)\$\$([^\$]*?)\$\$(.*)$/m;
            RE_INLINEMATH = /^([^\$]*?)\$([^\$]+?)\$(.*)$/m;
            ESCAPED_DOLLAR = '@@ESCAPED_D@@';
            ESCAPED_BACKSLASH = '@@ESCAPED_B@@';
            processedText = "";
            $div = $("<div>").html(text);
            $div.find("code").each(function(index, code) {
                codeArchive.push($(code).html());
                return $(code).html(codeArchive.length - 1);
            });
            text = $div.html();
            text = text.replace(/\\\$/g, ESCAPED_DOLLAR);
            // suppressing Don't make functions within a loop.
            /* jshint -W083 */
            while (true) {
                if (RE_INLINEMATH.test(text)) {
                    text = text.replace(RE_INLINEMATH, function($0, $1, $2, $3) {
                        processedText += $1 + processor("$" + $2 + "$", 'inline');
                        return $3;
                    });
                } else if (RE_DISPLAYMATH.test(text)) {
                    text = text.replace(RE_DISPLAYMATH, function($0, $1, $2, $3) {
                        /*
                         bug fix, ordering is off
                         */
                        processedText = processor("$$" + $2 + "$$", 'display') + processedText;
                        processedText = $1 + processedText;
                        return $3;
                    });
                } else {
                    processedText += text;
                    break;
                }
            }
            /* jshint +W083 */
            text = processedText;
            text = text.replace(new RegExp(ESCAPED_DOLLAR, 'g'), '\\$');
            text = text.replace(/\\\\\\\\/g, ESCAPED_BACKSLASH);
            text = text.replace(/\\begin\{([a-z]*\*?)\}([\s\S]*?)\\end\{\1\}/img, function($0, $1, $2) {
                return processor(("\\begin{" + $1 + "}") + $2 + ("\\end{" + $1 + "}"));
            });
            text = text.replace(new RegExp(ESCAPED_BACKSLASH, 'g'), '\\\\\\\\');
            $div = $("<div>").html(text);
            cnt = 0;
            $div.find("code").each(function(index, code) {
                $(code).html(processor(codeArchive[cnt], 'code'));
                return cnt += 1;
            });
            text = $div.html();
            return text;
        };

        DiscussionUtil.unescapeHighlightTag = function(text) {
            return text.replace(
                /\&lt\;highlight\&gt\;/g,
                "<span class='search-highlight'>").replace(/\&lt\;\/highlight\&gt\;/g, "</span>"
            );
        };

        DiscussionUtil.stripHighlight = function(text) {
            return text.replace(
                /\&(amp\;)?lt\;highlight\&(amp\;)?gt\;/g, "").replace(/\&(amp\;)?lt\;\/highlight\&(amp\;)?gt\;/g, ""
            );
        };

        DiscussionUtil.stripLatexHighlight = function(text) {
            return this.processEachMathAndCode(text, this.stripHighlight);
        };

        DiscussionUtil.markdownWithHighlight = function(text) {
            var converter;
            text = text.replace(/^\&gt\;/gm, ">");
            converter = Markdown.getMathCompatibleConverter();
            text = this.unescapeHighlightTag(this.stripLatexHighlight(converter.makeHtml(text)));
            return text.replace(/^>/gm, "&gt;");
        };

        DiscussionUtil.abbreviateString = function(text, minLength) {
            if (text.length < minLength) {
                return text;
            } else {
                while (minLength < text.length && text[minLength] !== ' ') {
                    minLength++;
                }
                return text.substr(0, minLength) + gettext('…');
            }
        };

        DiscussionUtil.abbreviateHTML = function(html, minLength) {
            var $result, imagesToReplace, truncated_text;
            truncated_text = jQuery.truncate(html, {
                length: minLength,
                noBreaks: true,
                ellipsis: gettext('…')
            });
            $result = $("<div>" + truncated_text + "</div>");
            imagesToReplace = $result.find("img:not(:first)");
            if (imagesToReplace.length > 0) {
                $result.append("<p><em>Some images in this post have been omitted</em></p>");
            }
            imagesToReplace.replaceWith("<em>image omitted</em>");
            return $result.html();
        };

        DiscussionUtil.getPaginationParams = function(curPage, numPages, pageUrlFunc) {
            var delta, maxPage, minPage, pageInfo;
            delta = 2;
            minPage = Math.max(curPage - delta, 1);
            maxPage = Math.min(curPage + delta, numPages);
            pageInfo = function(pageNum) {
                return {
                    number: pageNum,
                    url: pageUrlFunc(pageNum)
                };
            };
            return {
                page: curPage,
                lowPages: _.range(minPage, curPage).map(pageInfo),
                highPages: _.range(curPage + 1, maxPage + 1).map(pageInfo),
                previous: curPage > 1 ? pageInfo(curPage - 1) : null,
                next: curPage < numPages ? pageInfo(curPage + 1) : null,
                leftdots: minPage > 2,
                rightdots: maxPage < numPages - 1,
                first: minPage > 1 ? pageInfo(1) : null,
                last: maxPage < numPages ? pageInfo(numPages) : null
            };
        };

        return DiscussionUtil;
    }).call(this);
}).call(window);
