const GuideSortCriteria = {
    CHANNEL_NAME: 0,
    CHANNEL_NUMBER: 1
};

const HttpCodes = {
    OK: 200,
    CREATED: 201,
    BAD_REQUEST: 400,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    CONFLICT: 409,
    UNPROCESSABLE_ENTITY: 422,
    SERVICE_UNAVAILABLE_ERROR: 503
};

const Providers = ['beast', 'coolasice', 'crystalclear', 'inferno', 'smoothStreams', 'vaderStreams'];

const SortOrder = {
    ASCENDING: 0,
    DESCENDING: 1
};

$(document).ready(function () {
    $(window).resize(ResizeModule.resizeWindow);

    ResizeModule.init();
    MenuModule.init();
    GuideModule.init();
    VideoPlayerModule.init();
    RecordingsModule.init();
    ConfigurationModule.init();
    SettingsModule.init();

    GuideModule.sortChannels(SettingsModule.getSelectedGuideSortBy(),
                             SettingsModule.getSelectedGuideSortOrder());
});

const ResizeModule = (function () {
    let _configurationDivs = null;
    let _contentDiv = null;
    let _dayImages = null;
    let _guideButton = null;
    let _guideGroupSelect = null;
    let _guideSettingsDiv = null;
    let _navigationBarButtonsDiv = null;
    let _navigationBarDiv = null;
    let _protocolImages = null;
    let _searchGuideInputText = null;
    let _separatorSpan = null;
    let _streamingSettingsDiv = null;
    let _videoDiv = null;
    let _viewPortHeight = null;
    let _viewPortWidth = null;

    const _resizeChannelLis = function () {
        const channelLis = $('[id$="_channelLi"]');
        const channelDetailsSpans = $('[id$="_channelDetailsSpan"]');

        let maximumChannelDetailsSpanWidth = -1;

        channelDetailsSpans.each(function () {
            const channelDetailsSpan = $(this);

            if (channelDetailsSpan.width() > maximumChannelDetailsSpanWidth) {
                maximumChannelDetailsSpanWidth = Math.ceil(channelDetailsSpan.width());
            }
        });

        let minimumChannelLiWidth = 0;

        if (_viewPortWidth < 601) {
            minimumChannelLiWidth = 32 + 76 + 32 + maximumChannelDetailsSpanWidth;
        } else {
            minimumChannelLiWidth = 32 + 85 + 76 + 32 + maximumChannelDetailsSpanWidth;
        }

        channelLis.css('min-width', minimumChannelLiWidth + 'px');
    };

    const _resizeNavigationBar = function () {
        _guideGroupSelect.css('width', '');
        _separatorSpan.show();
        _searchGuideInputText.css('width', '');

        if (_navigationBarButtonsDiv.height() > _guideButton.outerHeight()) {
            _guideGroupSelect.css('width', '100%');
            _separatorSpan.hide();
            _searchGuideInputText.css('width', '100%');
        }
    };

    const _resizeSettingsImages = function (images, maximumWidth) {
        if (maximumWidth < 92) {
            images.css('max-width', maximumWidth + 'px');
        } else {
            images.css('max-width', '92px');
        }
    };

    const _updateViewPortDimensions = function () {
        _viewPortHeight = $(window).height();
        _viewPortWidth = $(window).width();
    };

    const init = function () {
        _configurationDivs = $('[id$=ConfigurationDiv]');
        _contentDiv = $('#contentDiv');
        _dayImages = $('#1Image, #2Image, #3Image, #4Image, #5Image');
        _guideButton = $('#guideButton');
        _guideGroupSelect = $('#guideGroupSelect');
        _guideSettingsDiv = $('#guideSettingsDiv');
        _navigationBarButtonsDiv = $('#navigationBarButtonsDiv');
        _navigationBarDiv = $('#navigationBarDiv');
        _protocolImages = $('#hlsImage, #rtmpImage');
        _searchGuideInputText = $('#searchGuideInputText');
        _separatorSpan = $('#separatorSpan');
        _streamingSettingsDiv = $('#streamingSettingsDiv');
        _videoDiv = $('#videoDiv');

        resizeWindow();
    };

    const resizeContentDiv = function () {
        const navigationBarDivHeight = _navigationBarDiv.position().top +
                                       _navigationBarDiv.offset().top +
                                       _navigationBarDiv.outerHeight(true);
        const contentDivMarginTop = navigationBarDivHeight + 16;
        const contentDivMaximumHeight = _viewPortHeight - contentDivMarginTop - 16;

        _contentDiv.css({
                            'margin-top': contentDivMarginTop + 'px',
                            'max-height': contentDivMaximumHeight + 'px'
                        });
        _contentDiv.show();

        // noinspection JSValidateTypes
        _contentDiv.children().each(function () {
            $(this).css('max-height', contentDivMaximumHeight + 'px');
        });
    };

    const resizeGuideAndVideoDivs = function (videoDivRevealing) {
        _updateViewPortDimensions();

        const guideDiv = $('#guideDiv');

        let guideDivWidth = '100%';

        /*
         * 1- If the videoDiv is hidden then only display the guideDiv with 100% width
         * 2- If the videoDiv is not hidden or about to reveal and the viewport is in landscape mode
         *      a- Evenly split the available viewport width
         *      b- Display the videoDiv to the right of the guideDiv
         *      c- videoDiv is displayed with a 16:9 aspect ratio
         * 3- If the videoDiv is not hidden or about to reveal and the viewport is in portrait mode
         *      a- Calculate the height required to display the videoDiv using the maximum available width
         *      b- If the videoDiv height required is less than half the available height
         *          i- Split the available viewport height
         *          ii- Display the videoDiv below the guideDiv
         *          iii- videoDiv is displayed with a 16:9 aspect ratio
         *      c- If the videoDiv height required is less than half the available height
         *          i- Evenly split the available viewport height
         *          ii- Display the videoDiv below the guideDiv
         *          iii- videoDiv is displayed with a 16:9 aspect ratio
         */
        if (_viewPortWidth >= _viewPortHeight) {
            if ((_videoDiv.is(':visible')) || (videoDivRevealing)) {
                guideDivWidth = '50%';

                _videoDiv.addClass('w3-right');
                _videoDiv.css({
                                  'height': (_viewPortWidth - 32) * 0.5 * 9 / 16 + 'px',
                                  'padding-top': '',
                                  'width': '50%'
                              });
            }

            guideDiv.addClass('w3-left');
            guideDiv.css({
                             'height': '',
                             'width': guideDivWidth
                         });
        } else {
            const maximumContentDivHeight = parseInt(_contentDiv.css('max-height'));

            if ((_videoDiv.is(':visible')) || (videoDivRevealing)) {
                const idealVideoDivHeight = ((_viewPortWidth - 32) * 9 / 16) + 16;

                guideDiv.removeClass('w3-left');
                _videoDiv.removeClass('w3-right');

                if ((maximumContentDivHeight / 2) > idealVideoDivHeight) {
                    _videoDiv.css({
                                      'height': idealVideoDivHeight + 'px',
                                      'padding-top': '16px',
                                      'width': '100%'
                                  });

                    guideDiv.css({
                                     'height': (maximumContentDivHeight - idealVideoDivHeight) + 'px',
                                     'width': guideDivWidth
                                 });
                } else {
                    _videoDiv.css({
                                      'height': (maximumContentDivHeight / 2) + 'px',
                                      'padding-top': '16px',
                                      'width': (((maximumContentDivHeight - 16) / 2) * 16 / 9) + 'px'
                                  });

                    guideDiv.css({
                                     'height': (maximumContentDivHeight / 2) + 'px',
                                     'width': guideDivWidth
                                 });
                }
            } else {
                guideDiv.addClass('w3-left');

                guideDiv.css({
                                 'height': '',
                                 'width': guideDivWidth
                             });
            }
        }
    };

    const resizeNumberImages = function () {
        const maximumNumberImageWidth = Math.floor((_guideSettingsDiv.width() - 64 - 70) / 5);

        _resizeSettingsImages(_dayImages, maximumNumberImageWidth);
    };

    const resizeProtocolImages = function () {
        const maximumProtocolImageWidth = Math.floor((_streamingSettingsDiv.width() - 64 - 70) / 2);

        _resizeSettingsImages(_protocolImages, maximumProtocolImageWidth);
    };

    const resizeWindow = function () {
        _updateViewPortDimensions();
        _resizeNavigationBar();
        resizeContentDiv();
        _resizeChannelLis();
        resizeGuideAndVideoDivs();
    };

    return {
        init: init,
        resizeContentDiv: resizeContentDiv,
        resizeGuideAndVideoDivs: resizeGuideAndVideoDivs,
        resizeNumberImages: resizeNumberImages,
        resizeProtocolImages: resizeProtocolImages,
        resizeWindow: resizeWindow
    };
})();

const CommonModule = (function () {
    const resetAlertDiv = function (alertDivId) {
        const alertDiv = $('#' + alertDivId);
        // noinspection JSValidateTypes
        const alertDivChildren = alertDiv.children();
        const alertSpan = alertDivChildren.filter('span');
        const alertHeader = alertDivChildren.filter('h3');
        const alertParagraphs = alertDivChildren.filter('p');

        alertDiv.removeClass('w3-green w3-red w3-yellow');
        alertSpan.removeClass('w3-green w3-red w3-yellow');
        alertHeader.text('');
        alertParagraphs.text('');

        alertDiv.hide({duration: 1000});
    };

    return {
        resetAlertDiv: resetAlertDiv
    };
})();

const MenuModule = (function () {
    let _guideGroupSelect = null;
    let _menuButtons = null;
    let _searchGuideInputText = null;

    const init = function () {
        _guideGroupSelect = $('#guideGroupSelect');
        _menuButtons = $('#guideButton, #recordingsButton, #configurationButton, #monitorButton, #aboutButton');
        _searchGuideInputText = $('#searchGuideInputText');
    };

    const openTab = function (idPrefix) {
        $('#guideDiv, #recordingsDiv, #configurationDiv, #monitorDiv, #aboutDiv')
            .not('#' + idPrefix + 'Div')
            .hide({duration: 500});

        _menuButtons.not('#' + idPrefix + 'Button').removeClass('w3-dark-grey');

        if (idPrefix !== 'guide') {
            _guideGroupSelect.hide({
                                       duration: 0,
                                       done: function () {
                                           ResizeModule.resizeContentDiv();
                                       }
                                   });

            _searchGuideInputText.hide({
                                           duration: 0,
                                           done: function () {
                                               ResizeModule.resizeContentDiv();
                                           }
                                       });
        } else {
            _guideGroupSelect.show({
                                       duration: 0,
                                       done: function () {
                                           ResizeModule.resizeContentDiv();
                                       }
                                   });

            _searchGuideInputText.show({
                                           duration: 0,
                                           done: function () {
                                               ResizeModule.resizeContentDiv();
                                           }
                                       });
        }

        $('#' + idPrefix + 'Button').addClass('w3-dark-grey');

        $('#' + idPrefix + 'Div').show({
                                           duration: 500,
                                           done: function () {
                                               if ($(this).prop('id').indexOf('recordings') !== -1) {
                                                   let currentDateTimeInUTC = moment().utc();

                                                   // Refresh the recordings every 30 minutes
                                                   if (currentDateTimeInUTC.diff(
                                                       RecordingsModule.getDateTimeOfLastLiveRecordingsUpdateInUTC(),
                                                       'seconds',
                                                       true) > 1800) {
                                                       RecordingsModule.refreshRecordings('live');
                                                   }

                                                   if (currentDateTimeInUTC.diff(
                                                       RecordingsModule.getDateTimeOfLastPersistedRecordingsUpdateInUTC(),
                                                       'seconds',
                                                       true) > 1800) {
                                                       RecordingsModule.refreshRecordings('persisted');
                                                   }

                                                   if (currentDateTimeInUTC.diff(
                                                       RecordingsModule.getDateTimeOfLastScheduledRecordingsUpdateInUTC(),
                                                       'seconds',
                                                       true) > 1800) {
                                                       RecordingsModule.refreshRecordings('scheduled');
                                                   }
                                               }
                                           }
                                       });
    };

    return {
        init: init,
        openTab: openTab
    };
})();

const GuideModule = (function () {
    let _contentDiv = null;
    let _guideGroupSelect = null;
    let _lastSelectedGuideGroup = null;
    let _loadingDiv = null;
    let _loadingHeader = null;

    const clearProgramRadioButtonGroup = function (idPrefix, idSuffix) {
        const programRadioButtons = $('[name="' + idPrefix + '_programRadioButton_' + idSuffix + '"]');
        const programClearButton = $('[name="' + idPrefix + '_programClearButton_' + idSuffix + '"]');
        const programRecordButton = $('[name="' + idPrefix + '_programRecordButton_' + idSuffix + '"]');

        // Uncheck the programRadioButtons
        programRadioButtons.prop('checked', false);

        // Add the onchange event to the programRadioButtons
        programRadioButtons.attr('onchange', 'GuideModule.enableClearAndRecordButtons("' +
                                             idPrefix +
                                             '", "' +
                                             idSuffix +
                                             '")');

        // Disable the programClearButton
        programClearButton.addClass('w3-disabled');

        // Disable the programRecordButton
        programRecordButton.addClass('w3-disabled');
    };

    const enableClearAndRecordButtons = function (idPrefix, idSuffix) {
        // Remove the onchange event from the programRadioButtons
        $('[name="' + idPrefix + '_programRadioButton_' + idSuffix + '"]').removeAttr('onchange');

        // Enable the programClearButton
        $('[name="' + idPrefix + '_programClearButton_' + idSuffix + '"]').removeClass('w3-disabled');

        // Enable the programRecordButton
        $('[name="' + idPrefix + '_programRecordButton_' + idSuffix + '"]').removeClass('w3-disabled');
    };

    const init = function () {
        _contentDiv = $('#contentDiv');
        _guideGroupSelect = $('#guideGroupSelect');
        _lastSelectedGuideGroup = 'SmoothStreams';
        _loadingDiv = $('#loadingDiv');
        _loadingHeader = $('#loadingHeader');

        // Uncheck all programRadioButtons in the document
        $('#guideDiv :input').prop('checked', false);

        // Disable all programClearButtons in the document
        $('[name*="_programClearButton"]').addClass('w3-disabled');

        // Disable all programRecordButtons in the document
        $('[name*="_programRecordButton"]').addClass('w3-disabled');
    };

    const recordProgram = function (idPrefix, idSuffix) {
        // Get the value of the checked programRadioButton
        const checkedRadioButton = $('input[name="' +
                                     idPrefix +
                                     '_programRadioButton_' +
                                     idSuffix +
                                     '"]:checked');
        const checkedRadioButtonValue = checkedRadioButton.val();

        const labelText = checkedRadioButton.next().text();
        const labelTextTokens = labelText.split('|');
        const programTitle = $.trim(labelTextTokens[1]);

        const programAlertDiv = $('#' + idPrefix + '_programAlertDiv_' + idSuffix);

        const jqXHR = $.ajax({
                                 data: checkedRadioButtonValue,
                                 dataType: 'json',
                                 headers: {'Authorization': 'Basic {{ authorization_basic_password }}'},
                                 method: 'POST',
                                 timeout: 5000,
                                 url: '/recordings'
                             });

        jqXHR.done(function () {
            CommonModule.resetAlertDiv(programAlertDiv.prop('id'));

            // Set the color of the programAlertDiv
            programAlertDiv.addClass('w3-green');

            // Set the color of the programSpan
            $('#' + idPrefix + '_programSpan_' + idSuffix).addClass('w3-green');

            // Set the text of the programHeader
            $('#' + idPrefix + '_programHeader_' + idSuffix).text('Success');

            // Set the text of the programMessageParagraph
            $('#' + idPrefix + '_programMessageParagraph_' + idSuffix)
                .text('Recording of ' + programTitle + ' successfully scheduled!');

            // Show the programAlertDiv
            programAlertDiv.show({duration: 1000});

            RecordingsModule.refreshRecordings('live');
            RecordingsModule.refreshRecordings('scheduled');
        });

        jqXHR.fail(function (jqXHR) {
            if (jqXHR.status === HttpCodes.CONFLICT) {
                CommonModule.resetAlertDiv(programAlertDiv.prop('id'));

                // Set the color of the programAlertDiv
                programAlertDiv.addClass('w3-blue');

                // Set the color of the programSpan
                $('#' + idPrefix + '_programSpan_' + idSuffix).addClass('w3-blue');

                // Set the text of the programHeader
                $('#' + idPrefix + '_programHeader_' + idSuffix).text('Info');

                // Set the text of the programMessageParagraph
                $('#' + idPrefix + '_programMessageParagraph_' + idSuffix)
                    .text('Recording of "' + programTitle + '" is already scheduled');

                // Show the programAlertDiv
                programAlertDiv.show({duration: 1000});
            } else {
                CommonModule.resetAlertDiv(programAlertDiv.prop('id'));

                // Set the color of the programAlertDiv
                programAlertDiv.addClass('w3-red');

                // Set the color of the span
                $('#' + idPrefix + '_programSpan_' + idSuffix).addClass('w3-red');

                // Set the text of the programHeader
                $('#' + idPrefix + '_programHeader_' + idSuffix).text('Error');

                // Set the text of the programMessageParagraph
                $('#' + idPrefix + '_programMessageParagraph_' + idSuffix)
                    .text('Failed to schedule recording of "' + programTitle + '"');

                if (jqXHR.status === 0) {
                    // Set the text of the programReasonParagraph
                    $('#' + idPrefix + '_programReasonParagraph_' + idSuffix)
                        .text('Check if IPTVProxy is up and running');
                } else {
                    // Set the text of the programReasonParagraph
                    $('#' + idPrefix + '_programReasonParagraph_' + idSuffix)
                        .text(JSON.parse(jqXHR.responseText)['errors'][0]['user_message']);
                }

                // Show the programAlertDiv
                programAlertDiv.show({duration: 1000});
            }
        });
    };

    const searchGuide = function () {
        const noMatchingProgramLi = $('#noMatchingProgramLi');

        if ($('#searchGuideInputText').val()) {
            const matchingLabels = $('[id*="_label_"]').filter(function () {
                return $(this).text().toUpperCase().indexOf($('#searchGuideInputText').val().toUpperCase()) !==
                       -1;
            });

            $('[id*="_buttonsLi_"]').hide();
            $('[id*="_programAlertDiv_"]').hide();
            $('[id*="_alertLi_"]').hide();
            $('[id*="_separatorLi_"]').hide();
            $('[id*="_programLi_"]').hide();
            $('[id*="_dateProgramsUl_"]').hide();
            $('[id*="_dateSeparatorLi_"]').hide();
            $('[id*="_dateProgramsLi_"]').hide();
            $('[id*="_dateLi_"]').hide();
            $('[id$="_channelProgramsUl"]').hide();
            noMatchingProgramLi.hide();
            $('[id$="_channelProgramsLi"]').hide();
            $('[id$="_channelLi"]').hide();

            $('[id*="_dateSpan_"]').each(function () {
                if ($(this).hasClass('fa-minus')) {
                    $(this).toggleClass('fa-minus fa-plus');
                }
            });
            $('[id$="_channelFoldingSpan"]').each(function () {
                if ($(this).hasClass('fa-minus')) {
                    $(this).toggleClass('fa-minus fa-plus');
                }
            });

            if (matchingLabels.length) {
                const programLisToShow = matchingLabels.parent('[id*="_programLi_"]');

                const dateProgramsUlsToShow = programLisToShow.parents('[id*="_dateProgramsUl_"]');
                const dateProgramsLisToShow = programLisToShow.parents('[id*="_dateProgramsLi_"]');
                const dateLisToShow = dateProgramsLisToShow.prev('[id*="_dateLi_"]');
                const dateSeparatorLisToShow = dateProgramsLisToShow.next('[id*="_dateSeparatorLi_"]');

                const channelProgramsUlsToShow = programLisToShow.parents('[id$="_channelProgramsUl"]');
                const channelProgramsLisToShow = programLisToShow.parents('[id$="_channelProgramsLi"]');
                const channelLiToShow = channelProgramsLisToShow.prev('[id$="_channelLi"]');

                const nextLisToShow = programLisToShow.map(function () {
                    return $(this)
                        .nextAll(
                            '[id*="_separatorLi_"]:first, [id*="_alertLi_"]:first, [id*="_buttonsLi_"]:first')
                        .get();
                });

                channelLiToShow.map(function () {
                    return $(this).find('[id$="_channelFoldingSpan"]:first').get();
                }).each(function () {
                    $(this).removeClass('fa-plus');
                    $(this).addClass('fa-minus');
                });

                dateLisToShow.map(function () {
                    return $(this).find('[id*="_dateSpan_"]:first').get();
                }).each(function () {
                    $(this).removeClass('fa-plus');
                    $(this).addClass('fa-minus');
                });

                channelLiToShow.show();
                channelProgramsLisToShow.show();
                channelProgramsUlsToShow.show();
                dateLisToShow.show();
                dateProgramsLisToShow.show();
                dateSeparatorLisToShow.show();
                dateProgramsUlsToShow.show();
                programLisToShow.show();
                nextLisToShow.show();
            } else {
                noMatchingProgramLi.show();
            }
        } else {
            $('[id*="_dateSpan_"]').each(function () {
                if ($(this).hasClass('fa-minus')) {
                    $(this).toggleClass('fa-minus fa-plus');
                }
            });
            $('[id$="_channelFoldingSpan"]').each(function () {
                if ($(this).hasClass('fa-minus')) {
                    $(this).toggleClass('fa-minus fa-plus');
                }
            });

            $('[id*="_buttonsLi_"]').show();
            $('[id*="_alertLi_"]').show();
            $('[id*="_separatorLi_"]').show();
            $('[id*="_programLi_"]').show();
            $('[id*="_dateProgramsUl_"]').show();
            $('[id*="_dateSeparatorLi_"]').show();
            $('[id*="_dateProgramsLi_"]').hide();
            $('[id*="_dateLi_"]').show();
            $('[id$="_channelProgramsUl"]').show();
            noMatchingProgramLi.hide();
            $('[id$="_channelProgramsLi"]').hide();
            $('[id$="_channelLi"]').show();
        }
    };

    const sortChannels = function (criteria, order) {
        const guideUl = $('#guideUl');
        const channelLis = $('[id$="_channelLi"]');

        channelLis.each(function () {
            const channelLi = $(this);

            channelLi.removeClass('w3-border-0')
        });

        channelLis.sort(function (a, b) {
            const aChannelLi = $(a);
            const bChannelLi = $(b);

            const aChannelDetailsSpan = aChannelLi.find('[id$="_channelDetailsSpan"]:first')
                                                  .text();
            const bChannelDetailsSpan = bChannelLi.find('[id$="_channelDetailsSpan"]:first')
                                                  .text();

            const aMatch = aChannelDetailsSpan.match(/(\d+) - (.*)/);
            const bMatch = bChannelDetailsSpan.match(/(\d+) - (.*)/);

            if (order === SortOrder.ASCENDING) {
                if (criteria === GuideSortCriteria.CHANNEL_NAME) {
                    if (aMatch[2] < bMatch[2]) {
                        return -1
                    } else if (aMatch[2] > bMatch[2]) {
                        return 1
                    }

                    return 0;
                } else if (criteria === GuideSortCriteria.CHANNEL_NUMBER) {
                    return parseInt(aMatch[1]) - parseInt(bMatch[1]);
                } else {
                    return 0;
                }
            } else if (order === SortOrder.DESCENDING) {
                if (criteria === GuideSortCriteria.CHANNEL_NAME) {
                    if (bMatch[2] < aMatch[2]) {
                        return -1
                    } else if (bMatch[2] > aMatch[2]) {
                        return 1
                    }

                    return 0;
                } else if (criteria === GuideSortCriteria.CHANNEL_NUMBER) {
                    return parseInt(bMatch[1]) - parseInt(aMatch[1]);
                } else {
                    return 0;
                }
            } else {
                return 0;
            }
        }).appendTo(guideUl);

        $('[id$="_channelProgramsLi"]').each(function () {
            const channelProgramsLi = $(this);
            const channelProgramsLiId = channelProgramsLi.prop('id');

            channelLis.each(function () {
                const channelLi = $(this);
                const channelLiId = channelLi.prop('id');

                if (channelLiId.split('_')[0] === channelProgramsLiId.split('_')[0]) {
                    channelProgramsLi.insertAfter(channelLi);

                    return false;
                }
            });
        });

        channelLis.last().addClass('w3-border-0');

        $('#noMatchingProgramLi').appendTo(guideUl);

        guideUl.show();
    };

    const toggleDateProgramsLi = function (idPrefix, idSuffix) {
        const dateSpanToToggle = $('#' + idPrefix + '_dateSpan_' + idSuffix);

        dateSpanToToggle.toggleClass('fa-minus fa-plus');

        // Toggle the dateProgramsLi
        $('#' + idPrefix + '_dateProgramsLi_' + idSuffix).toggle();
    };

    const toggleChannelProgramsLi = function (idPrefix) {
        const channelSpansToCollapse = $('[id$="_channelFoldingSpan"]')
            .not('#' + idPrefix + '_channelFoldingSpan');

        channelSpansToCollapse.removeClass('fa-minus');
        channelSpansToCollapse.addClass('fa-plus');

        // Hide all channelProgramsLi in the document except this programLi
        $('[id$="_channelProgramsLi"]').not('#' + idPrefix + '_channelProgramsLi').hide({duration: 1000});

        const channelSpanToToggle = $('#' + idPrefix + '_channelFoldingSpan');

        channelSpanToToggle.toggleClass('fa-minus fa-plus');

        // Toggle the channelProgramsLi
        $('#' + idPrefix + '_channelProgramsLi').toggle();
    };

    const updateGroup = function () {
        _guideGroupSelect.addClass('w3-disabled');

        const guideGroupSelectValue = _guideGroupSelect.val();
        const guideGroupSelectValueToken = guideGroupSelectValue.split('|');
        const guideProvider = guideGroupSelectValueToken[0];
        const guideGroup = guideGroupSelectValueToken[1];

        const settings_cookie_expires = Cookies.get('settings_cookie_expires')
                                               .replace(/\\(\d{3})/g, function (match, octal) {
                                                   return String.fromCharCode(parseInt(octal, 8));
                                               });

        if (settings_cookie_expires) {
            const expires = moment(settings_cookie_expires).utc().toDate();

            Cookies.set('guide_provider', guideProvider, {
                expires: expires,
                path: '/index.html'
            });

            Cookies.set('guide_group', guideGroup, {
                expires: expires,
                path: '/index.html'
            });
        }

        _loadingHeader.text('Updating guide from ' +
                            _lastSelectedGuideGroup +
                            ' to ' +
                            guideGroup);

        _loadingDiv.show();

        const jqXHR = $.ajax({
                                 dataType: 'html',
                                 method: 'GET',
                                 timeout: 0,
                                 url: '/index.html?refresh_epg=1'
                             });

        jqXHR.done(function (data) {
            if (data.startsWith('    <div')) {
                const guideDiv = $('#guideDiv');

                guideDiv.remove();

                _contentDiv.prepend(data);

                ResizeModule.resizeContentDiv();
                ResizeModule.resizeGuideAndVideoDivs();

                _lastSelectedGuideGroup = guideGroup;

                _guideGroupSelect.removeClass('w3-disabled');

                GuideModule.sortChannels(SettingsModule.getSelectedGuideSortBy(),
                                         SettingsModule.getSelectedGuideSortOrder());

                _loadingDiv.hide();
            } else {
                const headInnerHtml = data.substring(data.indexOf('<head>') + 6, data.indexOf('</head>'));
                const bodyInnerHtml = data.substring(data.indexOf('<body>') + 6, data.indexOf('</body>'));

                $('head').html(headInnerHtml);
                $('body').html(bodyInnerHtml);

                _guideGroupSelect.removeClass('w3-disabled');

                _loadingDiv.hide();
            }
        });

        jqXHR.fail(function () {
            _guideGroupSelect.removeClass('w3-disabled');

            _loadingDiv.hide();

            if ((jqXHR.status === HttpCodes.NOT_FOUND) || (jqXHR.status === HttpCodes.SERVICE_UNAVAILABLE_ERROR)) {
                location.reload();
            }
        });
    };

    return {
        clearProgramRadioButtonGroup: clearProgramRadioButtonGroup,
        enableClearAndRecordButtons: enableClearAndRecordButtons,
        init: init,
        recordProgram: recordProgram,
        searchGuide: searchGuide,
        sortChannels: sortChannels,
        toggleDateProgramsLi: toggleDateProgramsLi,
        toggleChannelProgramsLi: toggleChannelProgramsLi,
        updateGroup: updateGroup
    }
})();

const VideoPlayerModule = (function () {
    const DEFAULT_STREAMING_PROTOCOL = 'hls';

    let _currentControlSpan = null;
    let _lastPlayedVideoDetails = null;
    let _lastPlayedVideoSources = null;
    let _lastPlayedVideoSourceType = null;
    let _overlays = null;
    let _previousControlSpan = null;
    let _videoDiv = null;
    let _videoPlayer = null;

    const _constructOverlays = function (mediaInfoInnerHTML) {
        if (!_overlays) {
            const closeVideoDivInnerHTML = '<button id="videoDivCloseButton"' +
                                           '        class="w3-btn w3-circle w3-hover-black w3-small w3-transparent"' +
                                           '        onclick="VideoPlayerModule.closeVideoDiv()"' +
                                           '        style="height: 40px; width: 40px;">&times;</button>';
            _overlays = [{
                align: 'top-right',
                content: closeVideoDivInnerHTML,
                showBackground: false,
                start: 'useractive',
                end: 'userinactive'
            }];
        }

        if (mediaInfoInnerHTML) {
            if (_overlays.length === 4) {
                _overlays.pop();
                _overlays.pop();
                _overlays.pop();
            }

            _overlays.push({
                               align: 'top',
                               content: mediaInfoInnerHTML,
                               showBackground: true,
                               start: 'play',
                               end: 5
                           });
            _overlays.push({
                               align: 'top',
                               content: mediaInfoInnerHTML,
                               showBackground: true,
                               start: 'useractive',
                               end: 'userinactive'
                           });
            _overlays.push({
                               align: 'top',
                               content: mediaInfoInnerHTML,
                               showBackground: true,
                               start: 'pause',
                               end: 'play'
                           });
        }
    };

    const _constructVideoPlayer = function () {
        _videoDiv.append($('<video>')
                             .addClass('video-js vjs-big-play-centered vjs-default-skin')
                             .attr('data-setup',
                                   '{ "autoplay": false, "controls": true, "fluid": true, "preload": "auto" }')
                             .prop('id', 'videoPlayer'));

        _videoPlayer = videojs('videoPlayer');

        _videoPlayer.on('error', function () {
            this.error(null);
        });

        _videoPlayer.on('pause', function () {
            if ((_previousControlSpan) && (_previousControlSpan.hasClass('fa-pause'))) {
                _previousControlSpan.toggleClass('fa-pause fa-play');
            } else if (_currentControlSpan.hasClass('fa-pause')) {
                _currentControlSpan.toggleClass('fa-pause fa-play');
            }
        });

        _videoPlayer.on('play', function () {
            _currentControlSpan.toggleClass('fa-pause fa-play');
        });

        _constructOverlays(null);

        // noinspection JSUnresolvedFunction
        _videoPlayer.overlay({overlays: _overlays});
    };

    const _destructVideoPlayer = function () {
        _videoPlayer.dispose();

        _videoPlayer = null;

        if (_currentControlSpan) {
            _currentControlSpan.removeClass('fa-pause');
            _currentControlSpan.addClass('fa-play');
        }
    };

    const _playVideo = function (videoSource,
                                 videoType,
                                 videoSourceType,
                                 videoSources,
                                 videoDetails,
                                 protocol) {
        _videoPlayer.src({
                             src: videoSource,
                             type: videoType
                         });

        _videoPlayer.ready(function () {
            _videoPlayer.play();

            const mediaInfoInnerHTML = '<span>' + videoDetails + ' (' + protocol + ')</span>';
            _constructOverlays(mediaInfoInnerHTML);

            // noinspection JSUnresolvedFunction
            _videoPlayer.overlay({
                                     overlays: _overlays
                                 });

            _videoPlayer.on('playing', function () {
                _lastPlayedVideoSources = videoSources;
                _lastPlayedVideoDetails = videoDetails;
                _lastPlayedVideoSourceType = videoSourceType;
            });
        });
    };

    const _showVideoDiv = function () {
        if (!_videoDiv.is(':visible')) {
            _constructVideoPlayer();

            ResizeModule.resizeGuideAndVideoDivs(true);

            _videoDiv.show();
        }
    };

    const closeVideoDiv = function () {
        _destructVideoPlayer();

        _lastPlayedVideoSources = null;
        _lastPlayedVideoDetails = null;

        _videoDiv.hide();

        ResizeModule.resizeGuideAndVideoDivs(false);
    };

    const controlVideo = function (event) {
        _showVideoDiv();

        const eventTarget = $(event.target);

        if (eventTarget.hasClass('fa-play')) {
            if (isVideoPlaying()) {
                _previousControlSpan = _currentControlSpan;

                pauseVideo();
            }

            _currentControlSpan = eventTarget;

            const videoSources = eventTarget.data('json');
            const videoSourceType = videoSources['type'];

            if (videoSourceType === 'live') {
                playVideo(videoSourceType,
                          videoSources,
                          eventTarget.parents('[id$="channelLi"]')
                                     .find('[id$="_channelDetailsSpan"]:first')
                                     .text());
            } else {
                const controlColumn = eventTarget.parent();
                const programTitleColumn = controlColumn.next().next().next();
                const startDateTimeColumn = programTitleColumn.next();
                const endDateTimeColumn = startDateTimeColumn.next();


                playVideo(videoSourceType,
                          videoSources,
                          programTitleColumn.text() +
                          ' [' +
                          startDateTimeColumn.text() +
                          ' - ' +
                          endDateTimeColumn.text() +
                          ']');
            }
        } else {
            pauseVideo();
        }
    };

    const getLastPlayedVideoDetails = function () {
        return _lastPlayedVideoDetails;
    };

    const getLastPlayedVideoSources = function () {
        return _lastPlayedVideoSources;
    };

    const getLastPlayedVideoSourceType = function () {
        return _lastPlayedVideoSourceType;
    };

    const init = function () {
        _videoDiv = $('#videoDiv');
    };

    const isVideoPlaying = function () {
        if (_videoDiv.is(':visible')) {
            return !_videoPlayer.paused();
        }

        return false;
    };

    const pauseVideo = function () {
        _videoPlayer.pause();
    };

    const playVideo = function (videoSourceType, videoSources, videoDetails) {
        let selectedProtocol = SettingsModule.getSelectedStreamingProtocol();

        if ((videoSourceType === 'vod') || !(selectedProtocol in videoSources)) {
            selectedProtocol = DEFAULT_STREAMING_PROTOCOL;
        }

        const videoSource = videoSources[selectedProtocol]['videoSource'];
        // const videoType = videoSources[selectedProtocol]['videoType'];

        if ((videoSourceType === 'vod') || (selectedProtocol === 'hls')) {
            // const videoSource = videoSources[selectedProtocol]['videoSource'];
            // const videoType = videoSources[selectedProtocol]['videoType'];

            _playVideo(videoSource,
                       'application/vnd.apple.mpegurl',
                       videoSourceType,
                       videoSource,
                       videoDetails,
                       'HLS');
        } else if (selectedProtocol === 'rtmp') {
            const jqXHR = $.ajax({
                                     method: 'GET',
                                     timeout: 5000,
                                     url: videoSource
                                 });

            jqXHR.done(function (data) {
                const parser = new m3u8Parser.Parser();
                parser.push(data);
                parser.end();

                _playVideo(parser.manifest['segments'][0]['uri'],
                           'rtmp/mp4',
                           videoSourceType,
                           videoSource,
                           videoDetails,
                           'RTMP');
            });
        }
    };

    return {
        closeVideoDiv: closeVideoDiv,
        controlVideo: controlVideo,
        getLastPlayedVideoDetails: getLastPlayedVideoDetails,
        getLastPlayedVideoSources: getLastPlayedVideoSources,
        getLastPlayedVideoSourceType: getLastPlayedVideoSourceType,
        init: init,
        isVideoPlaying: isVideoPlaying,
        pauseVideo: pauseVideo,
        playVideo: playVideo
    }
})();

const RecordingsModule = (function () {
    let _currentDateTimeInUTC = null;
    let _dateTimeOfLastLiveRecordingsUpdateInUTC = null;
    let _dateTimeOfLastPersistedRecordingsUpdateInUTC = null;
    let _dateTimeOfLastScheduledRecordingsUpdateInUTC = null;
    let _liveRecordingsRefreshIcon = null;
    let _noRecordingsLis = null;
    let _recordingsActionButton = null;
    let _recordingsAlertDiv = null;
    let _recordingsClearButton = null;
    let _recordingsHeader = null;
    let _recordingsLis = null;
    let _recordingsMessageParagraph = null;
    let _recordingsReasonParagraph = null;
    let _recordingsSpan = null;
    let _recordingsTables = null;

    const _disableClearAndActionButtons = function () {
        // Disable the recordingsClearButton
        _recordingsClearButton.addClass('w3-disabled');

        // Disable the recordingsActionButton
        _recordingsActionButton.addClass('w3-disabled');

        // Clear the label of the recordingsActionButton
        _recordingsActionButton.html('-');
    };

    const _doDisableClearAndActionButtons = function () {
        // Is any recordingsRadioButton checked
        return !($('input[name="recordingsRadioButton"]').is(':checked'));
    };

    const _initTableSorter = function () {
        // Initialize tablesorter
        _recordingsTables['live'].tablesorter({
                                                  headers: {0: {sorter: false}}, sortList: [[1, 0], [4, 0]]
                                              });
        _recordingsTables['persisted'].tablesorter({
                                                       headers: {0: {sorter: false}}, sortList: [[1, 0], [4, 0]]
                                                   });
        _recordingsTables['scheduled'].tablesorter({
                                                       headers: {0: {sorter: false}}, sortList: [[1, 0], [4, 0]]
                                                   });
    };

    const _updateDateTimeOfLastRecordingsUpdate = function (type) {
        _currentDateTimeInUTC = moment.utc();

        if (type === 'live') {
            _dateTimeOfLastLiveRecordingsUpdateInUTC = _currentDateTimeInUTC
        } else if (type === 'persisted') {
            _dateTimeOfLastPersistedRecordingsUpdateInUTC = _currentDateTimeInUTC
        } else if (type === 'scheduled') {
            _dateTimeOfLastScheduledRecordingsUpdateInUTC = _currentDateTimeInUTC
        }
    };

    const _updateRecordingsTable = function (data, type) {
        const recordingsTable = _recordingsTables[type];

        // Delete all but the first row in the recordingsTable
        recordingsTable.find('tr:gt(0)').remove();

        const recordings = data['data'];

        if (recordings.length > 0) {
            for (let i = 0; i < recordings.length; i++) {
                let controlSpanDisplay = 'none';
                let spacingSpanDisplay = 'none';

                const playlistUrl = recordings[i].attributes.playlist_url;

                if (playlistUrl) {
                    controlSpanDisplay = 'inline-block';
                    spacingSpanDisplay = 'inline-block';
                }

                recordingsTable.find('tbody')
                               .append($('<tr>')
                                           .append($('<td>')
                                                       .append('<input class="w3-cell-middle"' +
                                                               '       onchange="RecordingsModule.enableClearAndActionButtons()"' +
                                                               '       name="recordingsRadioButton"' +
                                                               '       title="Select recording"' +
                                                               '       type="radio"' +
                                                               '       value="' +
                                                               recordings[i].id +
                                                               '" />')
                                                       .append('\n')
                                                       .append('<span style="display: ' +
                                                               spacingSpanDisplay +
                                                               '; width: 4px;"></span>'
                                                       )
                                                       .append('\n')
                                                       .append('<span class="w3-cell-middle fa fa-play"' +
                                                               '      data-json=\'{"type": "vod","hls": {"videoSource": "' +
                                                               playlistUrl +
                                                               '","videoType": "application/vnd.apple.mpegurl"}}\'' +
                                                               '      onclick="VideoPlayerModule.controlVideo(event)"' +
                                                               '      style="cursor: pointer; display: ' +
                                                               controlSpanDisplay +
                                                               ';"></span>'
                                                       )
                                           )
                                           .append($('<td>')
                                                       .text(recordings[i].attributes.channel_number)
                                           )
                                           .append($('<td>')
                                                       .text(recordings[i].attributes.channel_name)
                                           )
                                           .append($('<td>')
                                                       .text(recordings[i].attributes.program_title)
                                           )
                                           .append($('<td>')
                                                       .text(moment(recordings[i].attributes.start_date_time_in_utc,
                                                                    'YYYY-MM-DD HH:mm:ssZ')
                                                                 .format('YYYY-MM-DD HH:mm:ss'))
                                           )
                                           .append($('<td>')
                                                       .text(moment(recordings[i].attributes.end_date_time_in_utc,
                                                                    'YYYY-MM-DD HH:mm:ssZ')
                                                                 .format('YYYY-MM-DD HH:mm:ss'))
                                           )
                               );
            }

            recordingsTable.trigger('update');

            // Hide the NoRecordingLi
            _noRecordingsLis[type].hide({duration: 500});

            // Show the RecordingsLi
            _recordingsLis[type].show({duration: 500});
        } else {
            // Hide the RecordingsLi
            _recordingsLis[type].hide({duration: 500});

            // Show the NoRecordingsLi
            _noRecordingsLis[type].show({duration: 500});
        }
    };

    const clearRecordingsRadioButtonGroup = function () {
        // Uncheck all recordingsRadioButtons
        $('[name="recordingsRadioButton"]').prop('checked', false);

        _disableClearAndActionButtons();
    };

    const deleteRecording = function () {
        const checkedRadioButton = $('input[name="recordingsRadioButton"]:checked');

        const checkedRadioButtonValue = checkedRadioButton.val();
        const recordingTable = checkedRadioButton.closest('table');
        const recordingProgramTitle = checkedRadioButton.closest('td').next().next().next().html();


        if (checkedRadioButtonValue) {
            const jqXHR = $.ajax({
                                     dataType: 'json',
                                     headers: {'Authorization': 'Basic {{ authorization_basic_password }}'},
                                     method: 'DELETE',
                                     timeout: 5000,
                                     url: '/recordings/' + checkedRadioButtonValue
                                 });

            jqXHR.done(function () {
                CommonModule.resetAlertDiv(_recordingsAlertDiv.prop('id'));

                // Set the color of the recordingsAlertDiv
                _recordingsAlertDiv.addClass('w3-green');

                // Set the color of the recordingsSpan
                _recordingsSpan.addClass('w3-green');

                // Set the text of the recordingsHeader
                _recordingsHeader.text('Success');

                let action = '';
                if (recordingTable.prop('id').indexOf('live') !== -1) {
                    action = 'stopped';

                    refreshRecordings('live');
                    refreshRecordings('persisted');
                } else if (recordingTable.prop('id').indexOf('persisted') !== -1) {
                    action = 'deleted';

                    refreshRecordings('persisted');
                } else if (recordingTable.prop('id').indexOf('scheduled') !== -1) {
                    action = 'canceled';

                    refreshRecordings('scheduled');
                }

                // Set the text of the recordingsMessageParagraph
                _recordingsMessageParagraph
                    .text('Successfully ' + action + ' recording "' + recordingProgramTitle + '"');

                // Show the recordingsAlertDiv
                _recordingsAlertDiv.show({duration: 1000});

                // Scroll to the bottom of the page
                $('html, body').animate({scrollTop: $(document).height()});

                setTimeout(function () {
                    CommonModule.resetAlertDiv(_recordingsAlertDiv.prop('id'));
                }, 30000);
            });

            jqXHR.fail(function (jqXHR) {
                CommonModule.resetAlertDiv(_recordingsAlertDiv.prop('id'));

                // Set the color of the recordingsAlertDiv
                _recordingsAlertDiv.addClass('w3-red');

                // Set the color of the recordingsSpan
                _recordingsSpan.addClass('w3-red');

                // Set the text of the recordingsHeader
                _recordingsHeader.text('Error');

                let action = '';
                let type = '';
                if (recordingTable.prop('id').indexOf('live') !== -1) {
                    action = 'stop';
                    type = 'live';
                } else if (recordingTable.prop('id').indexOf('persisted') !== -1) {
                    action = 'delete';
                    type = 'persisted';
                } else if (recordingTable.prop('id').indexOf('scheduled') !== -1) {
                    action = 'cancel';
                    type = 'scheduled';
                }

                // Set the text of the recordingsMessageParagraph
                _recordingsMessageParagraph
                    .text('Failed to ' + action + ' recording "' + recordingProgramTitle + '"');

                if (jqXHR.status === HttpCodes.NOT_FOUND) {
                    // Set the text of the recordingsReasonParagraph
                    _recordingsReasonParagraph
                        .text(JSON.parse(jqXHR.responseText)['errors'][0]['user_message']);
                } else {
                    // Set the text of the recordingsReasonParagraph
                    _recordingsReasonParagraph.text('Encountered unexpected error');
                }

                // Show the recordingsAlertDiv
                _recordingsAlertDiv.show({duration: 1000});

                // Scroll to the bottom of the page
                $('html, body').animate({scrollTop: $(document).height()});

                refreshRecordings(type);
            });
        }
    };

    const enableClearAndActionButtons = function () {
        const recordingTable = $('input[name="recordingsRadioButton"]:checked').closest('table');

        // Enable the recordingsClearButton
        _recordingsClearButton.removeClass('w3-disabled');

        // Enable the recordingsActionButton
        _recordingsActionButton.removeClass('w3-disabled');

        if (recordingTable.prop('id').indexOf('live') !== -1) {
            _recordingsActionButton.html('Stop');
        } else if (recordingTable.prop('id').indexOf('persisted') !== -1) {
            _recordingsActionButton.html('Delete');
        } else if (recordingTable.prop('id').indexOf('scheduled') !== -1) {
            _recordingsActionButton.html('Cancel');
        }
    };

    const getDateTimeOfLastLiveRecordingsUpdateInUTC = function () {
        return _dateTimeOfLastLiveRecordingsUpdateInUTC;
    };

    const getDateTimeOfLastPersistedRecordingsUpdateInUTC = function () {
        return _dateTimeOfLastPersistedRecordingsUpdateInUTC;
    };

    const getDateTimeOfLastScheduledRecordingsUpdateInUTC = function () {
        return _dateTimeOfLastScheduledRecordingsUpdateInUTC;
    };

    const init = function () {
        _currentDateTimeInUTC = moment.utc();
        _dateTimeOfLastLiveRecordingsUpdateInUTC = _currentDateTimeInUTC;
        _dateTimeOfLastPersistedRecordingsUpdateInUTC = _currentDateTimeInUTC;
        _dateTimeOfLastScheduledRecordingsUpdateInUTC = _currentDateTimeInUTC;
        _liveRecordingsRefreshIcon = {
            'live': $('#liveRecordingsRefreshIcon'),
            'persisted': $('#persistedRecordingsRefreshIcon'),
            'scheduled': $('#scheduledRecordingsRefreshIcon')
        };
        _noRecordingsLis = {
            'live': $('#liveNoRecordingsLi'),
            'persisted': $('#persistedNoRecordingsLi'),
            'scheduled': $('#scheduledNoRecordingsLi')
        };
        _recordingsActionButton = $('#recordingsActionButton');
        _recordingsAlertDiv = $('#recordingsAlertDiv');
        _recordingsClearButton = $('#recordingsClearButton');
        _recordingsHeader = $('#recordingsHeader');
        _recordingsLis = {
            'live': $('#liveRecordingsLi'),
            'persisted': $('#persistedRecordingsLi'),
            'scheduled': $('#scheduledRecordingsLi')
        };
        _recordingsMessageParagraph = $('#recordingsMessageParagraph');
        _recordingsReasonParagraph = $('#recordingsReasonParagraph');
        _recordingsSpan = $('#recordingsSpan');
        _recordingsTables = {
            'live': $('#liveRecordingsTable'),
            'persisted': $('#persistedRecordingsTable'),
            'scheduled': $('#scheduledRecordingsTable'),
        };

        _initTableSorter();
        clearRecordingsRadioButtonGroup();
        _disableClearAndActionButtons();
    };

    const refreshRecordings = function (type) {
        const liveRecordingsRefreshIcon = _liveRecordingsRefreshIcon[type];

        liveRecordingsRefreshIcon.addClass('fa-spin');

        const jqXHR = $.ajax({
                                 dataType: 'json',
                                 headers: {'Authorization': 'Basic {{ authorization_basic_password }}'},
                                 method: 'GET',
                                 timeout: 5000,
                                 url: '/recordings?status=' + type
                             });

        jqXHR.done(function (data) {
            _updateDateTimeOfLastRecordingsUpdate(type);

            _updateRecordingsTable(data, type);

            if (_doDisableClearAndActionButtons()) {
                _disableClearAndActionButtons();
            }

            liveRecordingsRefreshIcon.removeClass('fa-spin')
        });

        jqXHR.fail(function () {
            CommonModule.resetAlertDiv(_recordingsAlertDiv.prop('id'));

            // Set the color of the recordingsAlertDiv
            _recordingsAlertDiv.addClass('w3-red');

            // Set the color of the recordingsSpan
            _recordingsSpan.addClass('w3-red');

            // Set the text of the recordingsHeader
            _recordingsHeader.text('Error');

            // Set the text of the recordingsMessageParagraph
            _recordingsMessageParagraph.text('Failed to refresh ' + type + ' recordings');

            if (jqXHR.status === 0) {
                // Set the text of the recordingsReasonParagraph
                _recordingsReasonParagraph.text('Check if IPTVProxy is up and running');
            }

            // Scroll to the bottom of the page
            $('html, body').animate({scrollTop: $(document).height()});

            // Show the recordingsAlertDiv
            _recordingsAlertDiv.show({duration: 1000});

            if (_doDisableClearAndActionButtons()) {
                _disableClearAndActionButtons();
            }

            liveRecordingsRefreshIcon.removeClass('fa-spin')
        });
    };

    return {
        clearRecordingsRadioButtonGroup: clearRecordingsRadioButtonGroup,
        deleteRecording: deleteRecording,
        enableClearAndActionButtons: enableClearAndActionButtons,
        getDateTimeOfLastLiveRecordingsUpdateInUTC: getDateTimeOfLastLiveRecordingsUpdateInUTC,
        getDateTimeOfLastPersistedRecordingsUpdateInUTC: getDateTimeOfLastPersistedRecordingsUpdateInUTC,
        getDateTimeOfLastScheduledRecordingsUpdateInUTC: getDateTimeOfLastScheduledRecordingsUpdateInUTC,
        init: init,
        refreshRecordings: refreshRecordings
    }
})();

const ConfigurationModule = (function () {
    let _beastConfigurationButton = null;
    let _beastConfigurationDiv = null;
    let _beastEnabledCheckbox = null;
    let _beastEpgSourceSelect = null;
    let _beastEpgUrlLabel = null;
    let _beastEpgUrlInput = null;
    let _beastPasswordInput = null;
    let _beastPlaylistProtocolSelect = null;
    let _beastPlaylistTypeSelect = null;
    let _beastTogglePasswordSpan = null;
    let _beastUsernameInput = null;
    let _configurationAlertDiv = null;
    let _configurationForm = null;
    let _configurationHeader = null;
    let _configurationMessageParagraph = null;
    let _configurationReasonParagraph = null;
    let _configurationResetButton = null;
    let _configurationSpan = null;
    let _coolAsIceConfigurationButton = null;
    let _coolAsIceConfigurationDiv = null;
    let _coolAsIceEnabledCheckbox = null;
    let _coolAsIceEpgSourceSelect = null;
    let _coolAsIceEpgUrlLabel = null;
    let _coolAsIceEpgUrlInput = null;
    let _coolAsIcePasswordInput = null;
    let _coolAsIcePlaylistProtocolSelect = null;
    let _coolAsIcePlaylistTypeSelect = null;
    let _coolAsIceTogglePasswordSpan = null;
    let _coolAsIceUsernameInput = null;
    let _crystalClearConfigurationButton = null;
    let _crystalClearConfigurationDiv = null;
    let _crystalClearEnabledCheckbox = null;
    let _crystalClearEpgSourceSelect = null;
    let _crystalClearEpgUrlLabel = null;
    let _crystalClearEpgUrlInput = null;
    let _crystalClearPasswordInput = null;
    let _crystalClearPlaylistProtocolSelect = null;
    let _crystalClearPlaylistTypeSelect = null;
    let _crystalClearTogglePasswordSpan = null;
    let _crystalClearUsernameInput = null;
    let _darkMediaConfigurationButton = null;
    let _darkMediaConfigurationDiv = null;
    let _darkMediaEnabledCheckbox = null;
    let _darkMediaEpgSourceSelect = null;
    let _darkMediaEpgUrlLabel = null;
    let _darkMediaEpgUrlInput = null;
    let _darkMediaPasswordInput = null;
    let _darkMediaPlaylistProtocolSelect = null;
    let _darkMediaPlaylistTypeSelect = null;
    let _darkMediaTogglePasswordSpan = null;
    let _darkMediaUsernameInput = null;
    let _errorSpans = null;
    let _helixConfigurationButton = null;
    let _helixConfigurationDiv = null;
    let _helixEnabledCheckbox = null;
    let _helixEpgSourceSelect = null;
    let _helixEpgUrlLabel = null;
    let _helixEpgUrlInput = null;
    let _helixPasswordInput = null;
    let _helixPlaylistProtocolSelect = null;
    let _helixPlaylistTypeSelect = null;
    let _helixTogglePasswordSpan = null;
    let _helixUsernameInput = null;
    let _infernoConfigurationButton = null;
    let _infernoConfigurationDiv = null;
    let _infernoEnabledCheckbox = null;
    let _infernoEpgSourceSelect = null;
    let _infernoEpgUrlLabel = null;
    let _infernoEpgUrlInput = null;
    let _infernoPasswordInput = null;
    let _infernoPlaylistProtocolSelect = null;
    let _infernoPlaylistTypeSelect = null;
    let _infernoTogglePasswordSpan = null;
    let _infernoUsernameInput = null;
    let _kingConfigurationButton = null;
    let _kingConfigurationDiv = null;
    let _kingEnabledCheckbox = null;
    let _kingEpgSourceSelect = null;
    let _kingEpgUrlLabel = null;
    let _kingEpgUrlInput = null;
    let _kingPasswordInput = null;
    let _kingPlaylistProtocolSelect = null;
    let _kingPlaylistTypeSelect = null;
    let _kingTogglePasswordSpan = null;
    let _kingUsernameInput = null;
    let _lastAppliedConfigurationSerialization = null;
    let _serverConfigurationButton = null;
    let _serverConfigurationDiv = null;
    let _serverHostnameLoopbackInput = null;
    let _serverHostnamePrivateInput = null;
    let _serverHostnamePublicInput = null;
    let _serverHttpPortInput = null;
    let _serverHttpsPortInput = null;
    let _serverPasswordInput = null;
    let _smoothStreamsConfigurationButton = null;
    let _smoothStreamsConfigurationDiv = null;
    let _smoothStreamsEnabledCheckbox = null;
    let _smoothStreamsEpgSourceSelect = null;
    let _smoothStreamsEpgUrlLabel = null;
    let _smoothStreamsEpgUrlInput = null;
    let _smoothStreamsPasswordInput = null;
    let _smoothStreamsPlaylistProtocolSelect = null;
    let _smoothStreamsPlaylistTypeSelect = null;
    let _smoothStreamsServerSelect = null;
    let _smoothStreamsServiceSelect = null;
    let _smoothStreamsTogglePasswordSpan = null;
    let _smoothStreamsUsernameInput = null;
    let _universeConfigurationButton = null;
    let _universeConfigurationDiv = null;
    let _universeEnabledCheckbox = null;
    let _universeEpgSourceSelect = null;
    let _universeEpgUrlLabel = null;
    let _universeEpgUrlInput = null;
    let _universePasswordInput = null;
    let _universePlaylistProtocolSelect = null;
    let _universePlaylistTypeSelect = null;
    let _universeTogglePasswordSpan = null;
    let _universeUsernameInput = null;
    let _updateConfigurationButton = null;
    let _vaderStreamsConfigurationButton = null;
    let _vaderStreamsConfigurationDiv = null;
    let _vaderStreamsEnabledCheckbox = null;
    let _vaderStreamsEpgSourceSelect = null;
    let _vaderStreamsEpgUrlLabel = null;
    let _vaderStreamsEpgUrlInput = null;
    let _vaderStreamsPasswordInput = null;
    let _vaderStreamsPlaylistProtocolSelect = null;
    let _vaderStreamsPlaylistTypeSelect = null;
    let _vaderStreamsServerSelect = null;
    let _vaderStreamsTogglePasswordSpan = null;
    let _vaderStreamsUsernameInput = null;

    const _clearConfigurationErrorMessages = function () {
        _serverPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _serverHttpPortInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _serverHttpsPortInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _serverHostnameLoopbackInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _serverHostnamePrivateInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _serverHostnamePublicInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _beastEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIceUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIcePasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIcePlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIcePlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIceEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _coolAsIceEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _crystalClearEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _darkMediaEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _helixEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _infernoEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _kingEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsServiceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsServerSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _smoothStreamsEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universeUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universePasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universePlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universePlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universeEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _universeEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsServerSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsUsernameInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsPasswordInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsPlaylistProtocolSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsPlaylistTypeSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsEpgSourceSelect.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        _vaderStreamsEpgUrlInput.removeClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');

        _errorSpans.text('');
    };

    const _disableProviderConfigurationInputs = function (provider) {
        const providerEpgSourceSelect = $('#' + provider + 'EpgSourceSelect');
        const providerEpgUrlInput = $('#' + provider + 'EpgUrlInput');
        const providerPasswordInput = $('#' + provider + 'PasswordInput');
        const providerPlaylistProtocolSelect = $('#' + provider + 'PlaylistProtocolSelect');
        const providerPlaylistTypeSelect = $('#' + provider + 'PlaylistTypeSelect');
        const providerServerSelect = $('#' + provider + 'ServerSelect');
        const providerServiceSelect = $('#' + provider + 'ServiceSelect');
        const providerUsernameInput = $('#' + provider + 'UsernameInput');

        if (providerEpgSourceSelect) {
            providerEpgSourceSelect.addClass('w3-disabled');
        }

        if (providerEpgUrlInput) {
            providerEpgUrlInput.addClass('w3-disabled');
        }

        if (providerPasswordInput) {
            providerPasswordInput.addClass('w3-disabled');
        }

        if (providerPlaylistProtocolSelect) {
            providerPlaylistProtocolSelect.addClass('w3-disabled');
        }

        if (providerPlaylistTypeSelect) {
            providerPlaylistTypeSelect.addClass('w3-disabled');
        }

        if (providerServerSelect) {
            providerServerSelect.addClass('w3-disabled');
        }

        if (providerServiceSelect) {
            providerServiceSelect.addClass('w3-disabled');
        }

        if (providerUsernameInput) {
            providerUsernameInput.addClass('w3-disabled');
        }
    };

    const _disableResetAndUpdateButtons = function () {
        // Disable the configurationResetButton
        _configurationResetButton.addClass('w3-disabled');

        // Disable the updateConfigurationButton
        _updateConfigurationButton.addClass('w3-disabled');
    };

    const _enableProviderConfigurationInputs = function (provider) {
        const providerEpgSourceSelect = $('#' + provider + 'EpgSourceSelect');
        const providerEpgUrlInput = $('#' + provider + 'EpgUrlInput');
        const providerPasswordInput = $('#' + provider + 'PasswordInput');
        const providerPlaylistProtocolSelect = $('#' + provider + 'PlaylistProtocolSelect');
        const providerPlaylistTypeSelect = $('#' + provider + 'PlaylistTypeSelect');
        const providerServerSelect = $('#' + provider + 'ServerSelect');
        const providerServiceSelect = $('#' + provider + 'ServiceSelect');
        const providerUsernameInput = $('#' + provider + 'UsernameInput');

        if (providerEpgSourceSelect) {
            providerEpgSourceSelect.removeClass('w3-disabled');
        }

        if (providerEpgUrlInput) {
            providerEpgUrlInput.removeClass('w3-disabled');
        }

        if (providerPasswordInput) {
            providerPasswordInput.removeClass('w3-disabled');
        }

        if (providerPlaylistProtocolSelect) {
            providerPlaylistProtocolSelect.removeClass('w3-disabled');
        }

        if (providerPlaylistTypeSelect) {
            providerPlaylistTypeSelect.removeClass('w3-disabled');
        }

        if (providerServerSelect) {
            providerServerSelect.removeClass('w3-disabled');
        }

        if (providerServiceSelect) {
            providerServiceSelect.removeClass('w3-disabled');
        }

        if (providerUsernameInput) {
            providerUsernameInput.removeClass('w3-disabled');
        }
    };

    const _enableResetAndUpdateButtons = function () {
        // Enable the configurationResetButton
        _configurationResetButton.removeClass('w3-disabled');

        // Enable the updateConfigurationButton
        _updateConfigurationButton.removeClass('w3-disabled');
    };

    const _serializeConfigurationForm = function () {
        _lastAppliedConfigurationSerialization = _configurationForm.serialize();
    };

    const determineEpgUrlLabelInputVisibility = function () {
        $.each(Providers, function (i, provider) {
            const providerEpgSourceSelect = $('#' + provider + 'EpgSourceSelect');
            const providerEpgUrlLabel = $('#' + provider + 'EpgUrlLabel');
            const providerEpgUrlInput = $('#' + provider + 'EpgUrlInput');

            if (providerEpgSourceSelect.val() === 'other') {
                providerEpgUrlLabel.show();
                providerEpgUrlInput.show();
            } else {
                providerEpgUrlLabel.hide();
                providerEpgUrlInput.hide();
            }
        });
    };

    const determineProviderConfigurationInputsState = function () {
        $.each(Providers, function (i, provider) {
            const providerEnabledCheckbox = $('#' + provider + 'EnabledCheckbox');

            if (providerEnabledCheckbox.is(':checked')) {
                _enableProviderConfigurationInputs(provider);
            } else {
                _disableProviderConfigurationInputs(provider);
            }
        });
    };

    const determineResetAndUpdateButtonsState = function () {
        const currentConfigurationSerialization = _configurationForm.serialize();

        if (currentConfigurationSerialization !== _lastAppliedConfigurationSerialization) {
            _enableResetAndUpdateButtons()
        } else {
            _disableResetAndUpdateButtons()
        }
    };

    const init = function () {
        _beastConfigurationButton = $('#beastConfigurationButton');
        _beastConfigurationDiv = $('#beastConfigurationDiv');
        _beastEnabledCheckbox = $('#beastEnabledCheckbox');
        _beastEpgSourceSelect = $('#beastEpgSourceSelect');
        _beastEpgUrlLabel = $('#beastEpgUrlLabel');
        _beastEpgUrlInput = $('#beastEpgUrlInput');
        _beastPasswordInput = $('#beastPasswordInput');
        _beastPlaylistProtocolSelect = $('#beastPlaylistProtocolSelect');
        _beastPlaylistTypeSelect = $('#beastPlaylistTypeSelect');
        _beastTogglePasswordSpan = $('#beastTogglePasswordSpan');
        _beastUsernameInput = $('#beastUsernameInput');
        _coolAsIceConfigurationButton = $('#coolAsIceConfigurationButton');
        _coolAsIceConfigurationDiv = $('#coolAsIceConfigurationDiv');
        _coolAsIceEnabledCheckbox = $('#coolAsIceEnabledCheckbox');
        _coolAsIceEpgSourceSelect = $('#coolAsIceEpgSourceSelect');
        _coolAsIceEpgUrlLabel = $('#coolAsIceEpgUrlLabel');
        _coolAsIceEpgUrlInput = $('#coolAsIceEpgUrlInput');
        _coolAsIcePasswordInput = $('#coolAsIcePasswordInput');
        _coolAsIcePlaylistProtocolSelect = $('#coolAsIcePlaylistProtocolSelect');
        _coolAsIcePlaylistTypeSelect = $('#coolAsIcePlaylistTypeSelect');
        _coolAsIceTogglePasswordSpan = $('#coolAsIceTogglePasswordSpan');
        _coolAsIceUsernameInput = $('#coolAsIceUsernameInput');
        _configurationAlertDiv = $('#configurationAlertDiv');
        _configurationForm = $('#configurationForm');
        _configurationHeader = $('#configurationHeader');
        _configurationMessageParagraph = $('#configurationMessageParagraph');
        _configurationReasonParagraph = $('#configurationReasonParagraph');
        _configurationResetButton = $('#configurationResetButton');
        _configurationSpan = $('#configurationSpan');
        _crystalClearConfigurationButton = $('#crystalClearConfigurationButton');
        _crystalClearConfigurationDiv = $('#crystalClearConfigurationDiv');
        _crystalClearEnabledCheckbox = $('#crystalClearEnabledCheckbox');
        _crystalClearEpgSourceSelect = $('#crystalClearEpgSourceSelect');
        _crystalClearEpgUrlLabel = $('#crystalClearEpgUrlLabel');
        _crystalClearEpgUrlInput = $('#crystalClearEpgUrlInput');
        _crystalClearPasswordInput = $('#crystalClearPasswordInput');
        _crystalClearPlaylistProtocolSelect = $('#crystalClearPlaylistProtocolSelect');
        _crystalClearPlaylistTypeSelect = $('#crystalClearPlaylistTypeSelect');
        _crystalClearTogglePasswordSpan = $('#crystalClearTogglePasswordSpan');
        _crystalClearUsernameInput = $('#crystalClearUsernameInput');
        _darkMediaConfigurationButton = $('#darkMediaConfigurationButton');
        _darkMediaConfigurationDiv = $('#darkMediaConfigurationDiv');
        _darkMediaEnabledCheckbox = $('#darkMediaEnabledCheckbox');
        _darkMediaEpgSourceSelect = $('#darkMediaEpgSourceSelect');
        _darkMediaEpgUrlLabel = $('#darkMediaEpgUrlLabel');
        _darkMediaEpgUrlInput = $('#darkMediaEpgUrlInput');
        _darkMediaPasswordInput = $('#darkMediaPasswordInput');
        _darkMediaPlaylistProtocolSelect = $('#darkMediaPlaylistProtocolSelect');
        _darkMediaPlaylistTypeSelect = $('#darkMediaPlaylistTypeSelect');
        _darkMediaTogglePasswordSpan = $('#darkMediaTogglePasswordSpan');
        _darkMediaUsernameInput = $('#darkMediaUsernameInput');
        _errorSpans = $('[id$=ErrorSpan]');
        _helixConfigurationButton = $('#helixConfigurationButton');
        _helixConfigurationDiv = $('#helixConfigurationDiv');
        _helixEnabledCheckbox = $('#helixEnabledCheckbox');
        _helixEpgSourceSelect = $('#helixEpgSourceSelect');
        _helixEpgUrlLabel = $('#helixEpgUrlLabel');
        _helixEpgUrlInput = $('#helixEpgUrlInput');
        _helixPasswordInput = $('#helixPasswordInput');
        _helixPlaylistProtocolSelect = $('#helixPlaylistProtocolSelect');
        _helixPlaylistTypeSelect = $('#helixPlaylistTypeSelect');
        _helixTogglePasswordSpan = $('#helixTogglePasswordSpan');
        _helixUsernameInput = $('#helixUsernameInput');
        _infernoConfigurationButton = $('#infernoConfigurationButton');
        _infernoConfigurationDiv = $('#infernoConfigurationDiv');
        _infernoEnabledCheckbox = $('#infernoEnabledCheckbox');
        _infernoEpgSourceSelect = $('#infernoEpgSourceSelect');
        _infernoEpgUrlLabel = $('#infernoEpgUrlLabel');
        _infernoEpgUrlInput = $('#infernoEpgUrlInput');
        _infernoPasswordInput = $('#infernoPasswordInput');
        _infernoPlaylistProtocolSelect = $('#infernoPlaylistProtocolSelect');
        _infernoPlaylistTypeSelect = $('#infernoPlaylistTypeSelect');
        _infernoTogglePasswordSpan = $('#infernoTogglePasswordSpan');
        _infernoUsernameInput = $('#infernoUsernameInput');
        _kingConfigurationButton = $('#kingConfigurationButton');
        _kingConfigurationDiv = $('#kingConfigurationDiv');
        _kingEnabledCheckbox = $('#kingEnabledCheckbox');
        _kingEpgSourceSelect = $('#kingEpgSourceSelect');
        _kingEpgUrlLabel = $('#kingEpgUrlLabel');
        _kingEpgUrlInput = $('#kingEpgUrlInput');
        _kingPasswordInput = $('#kingPasswordInput');
        _kingPlaylistProtocolSelect = $('#kingPlaylistProtocolSelect');
        _kingPlaylistTypeSelect = $('#kingPlaylistTypeSelect');
        _kingTogglePasswordSpan = $('#kingTogglePasswordSpan');
        _kingUsernameInput = $('#kingUsernameInput');
        _serverConfigurationButton = $('#serverConfigurationButton');
        _serverConfigurationDiv = $('#serverConfigurationDiv');
        _serverHostnameLoopbackInput = $('#serverHostnameLoopbackInput');
        _serverHostnamePrivateInput = $('#serverHostnamePrivateInput');
        _serverHostnamePublicInput = $('#serverHostnamePublicInput');
        _serverHttpPortInput = $('#serverHttpPortInput');
        _serverHttpsPortInput = $('#serverHttpsPortInput');
        _serverPasswordInput = $('#serverPasswordInput');
        _smoothStreamsConfigurationButton = $('#smoothStreamsConfigurationButton');
        _smoothStreamsConfigurationDiv = $('#smoothStreamsConfigurationDiv');
        _smoothStreamsEnabledCheckbox = $('#smoothStreamsEnabledCheckbox');
        _smoothStreamsEpgSourceSelect = $('#smoothStreamsEpgSourceSelect');
        _smoothStreamsEpgUrlLabel = $('#smoothStreamsEpgUrlLabel');
        _smoothStreamsEpgUrlInput = $('#smoothStreamsEpgUrlInput');
        _smoothStreamsPasswordInput = $('#smoothStreamsPasswordInput');
        _smoothStreamsPlaylistProtocolSelect = $('#smoothStreamsPlaylistProtocolSelect');
        _smoothStreamsPlaylistTypeSelect = $('#smoothStreamsPlaylistTypeSelect');
        _smoothStreamsServerSelect = $('#smoothStreamsServerSelect');
        _smoothStreamsServiceSelect = $('#smoothStreamsServiceSelect');
        _smoothStreamsTogglePasswordSpan = $('#smoothStreamsTogglePasswordSpan');
        _smoothStreamsUsernameInput = $('#smoothStreamsUsernameInput');
        _universeConfigurationButton = $('#universeConfigurationButton');
        _universeConfigurationDiv = $('#universeConfigurationDiv');
        _universeEnabledCheckbox = $('#universeEnabledCheckbox');
        _universeEpgSourceSelect = $('#universeEpgSourceSelect');
        _universeEpgUrlLabel = $('#universeEpgUrlLabel');
        _universeEpgUrlInput = $('#universeEpgUrlInput');
        _universePasswordInput = $('#universePasswordInput');
        _universePlaylistProtocolSelect = $('#universePlaylistProtocolSelect');
        _universePlaylistTypeSelect = $('#universePlaylistTypeSelect');
        _universeTogglePasswordSpan = $('#universeTogglePasswordSpan');
        _universeUsernameInput = $('#universeUsernameInput');
        _updateConfigurationButton = $('#updateConfigurationButton');
        _vaderStreamsConfigurationButton = $('#vaderStreamsConfigurationButton');
        _vaderStreamsConfigurationDiv = $('#vaderStreamsConfigurationDiv');
        _vaderStreamsEnabledCheckbox = $('#vaderStreamsEnabledCheckbox');
        _vaderStreamsEpgSourceSelect = $('#vaderStreamsEpgSourceSelect');
        _vaderStreamsEpgUrlLabel = $('#vaderStreamsEpgUrlLabel');
        _vaderStreamsEpgUrlInput = $('#vaderStreamsEpgUrlInput');
        _vaderStreamsPasswordInput = $('#vaderStreamsPasswordInput');
        _vaderStreamsPlaylistProtocolSelect = $('#vaderStreamsPlaylistProtocolSelect');
        _vaderStreamsPlaylistTypeSelect = $('#vaderStreamsPlaylistTypeSelect');
        _vaderStreamsServerSelect = $('#vaderStreamsServerSelect');
        _vaderStreamsTogglePasswordSpan = $('#vaderStreamsTogglePasswordSpan');
        _vaderStreamsUsernameInput = $('#vaderStreamsUsernameInput');

        _serializeConfigurationForm();
        determineProviderConfigurationInputsState();
        determineEpgUrlLabelInputVisibility();
    };

    const resetConfiguration = function () {
        _clearConfigurationErrorMessages();
        CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));

        const jqXHR = $.ajax({
                                 dataType: 'json',
                                 headers: {'Authorization': 'Basic {{ authorization_basic_password }}'},
                                 method: 'GET',
                                 timeout: 5000,
                                 url: '/configuration'
                             });

        jqXHR.done(function (data) {
            _serializeConfigurationForm();

            _clearConfigurationErrorMessages();
            CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));

            _serverPasswordInput.val(data['data']['attributes']['server_password']);
            _serverHttpPortInput.val(data['data']['attributes']['server_http_port']);
            _serverHttpsPortInput.val(data['data']['attributes']['server_https_port']);
            _serverHostnameLoopbackInput.val(data['data']['attributes']['server_hostname_loopback']);
            _serverHostnamePrivateInput.val(data['data']['attributes']['server_hostname_private']);
            _serverHostnamePublicInput.val(data['data']['attributes']['server_hostname_public']);
            _beastUsernameInput.val(data['data']['attributes']['beast_username']);
            _beastPasswordInput.val(data['data']['attributes']['beast_password']);
            _beastPlaylistProtocolSelect.val(data['data']['attributes']['beast_playlist_protocol'].toLowerCase());
            _beastPlaylistTypeSelect.val(data['data']['attributes']['beast_playlist_type'].toLowerCase());
            _beastEpgSourceSelect.val(data['data']['attributes']['beast_epg_source'].toLowerCase());
            _beastEpgUrlInput.val(data['data']['attributes']['beast_epg_url']);
            _coolAsIceUsernameInput.val(data['data']['attributes']['coolasice_username']);
            _coolAsIcePasswordInput.val(data['data']['attributes']['coolasice_password']);
            _coolAsIcePlaylistProtocolSelect.val(data['data']['attributes']['coolasice_playlist_protocol'].toLowerCase());
            _coolAsIcePlaylistTypeSelect.val(data['data']['attributes']['coolasice_playlist_type'].toLowerCase());
            _coolAsIceEpgSourceSelect.val(data['data']['attributes']['coolasice_epg_source'].toLowerCase());
            _coolAsIceEpgUrlInput.val(data['data']['attributes']['coolasice_epg_url']);
            _crystalClearUsernameInput.val(data['data']['attributes']['crystalclear_username']);
            _crystalClearPasswordInput.val(data['data']['attributes']['crystalclear_password']);
            _crystalClearPlaylistProtocolSelect.val(data['data']['attributes']['crystalclear_playlist_protocol'].toLowerCase());
            _crystalClearPlaylistTypeSelect.val(data['data']['attributes']['crystalclear_playlist_type'].toLowerCase());
            _crystalClearEpgSourceSelect.val(data['data']['attributes']['crystalclear_epg_source'].toLowerCase());
            _crystalClearEpgUrlInput.val(data['data']['attributes']['crystalclear_epg_url']);
            _darkMediaUsernameInput.val(data['data']['attributes']['darkMedia_username']);
            _darkMediaPasswordInput.val(data['data']['attributes']['darkMedia_password']);
            _darkMediaPlaylistProtocolSelect.val(data['data']['attributes']['darkMedia_playlist_protocol'].toLowerCase());
            _darkMediaPlaylistTypeSelect.val(data['data']['attributes']['darkMedia_playlist_type'].toLowerCase());
            _darkMediaEpgSourceSelect.val(data['data']['attributes']['darkMedia_epg_source'].toLowerCase());
            _darkMediaEpgUrlInput.val(data['data']['attributes']['darkMedia_epg_url']);
            _helixUsernameInput.val(data['data']['attributes']['helix_username']);
            _helixPasswordInput.val(data['data']['attributes']['helix_password']);
            _helixPlaylistProtocolSelect.val(data['data']['attributes']['helix_playlist_protocol'].toLowerCase());
            _helixPlaylistTypeSelect.val(data['data']['attributes']['helix_playlist_type'].toLowerCase());
            _helixEpgSourceSelect.val(data['data']['attributes']['helix_epg_source'].toLowerCase());
            _helixEpgUrlInput.val(data['data']['attributes']['helix_epg_url']);
            _infernoUsernameInput.val(data['data']['attributes']['inferno_username']);
            _infernoPasswordInput.val(data['data']['attributes']['inferno_password']);
            _infernoPlaylistProtocolSelect.val(data['data']['attributes']['inferno_playlist_protocol'].toLowerCase());
            _infernoPlaylistTypeSelect.val(data['data']['attributes']['inferno_playlist_type'].toLowerCase());
            _infernoEpgSourceSelect.val(data['data']['attributes']['inferno_epg_source'].toLowerCase());
            _infernoEpgUrlInput.val(data['data']['attributes']['inferno_epg_url']);
            _kingUsernameInput.val(data['data']['attributes']['king_username']);
            _kingPasswordInput.val(data['data']['attributes']['king_password']);
            _kingPlaylistProtocolSelect.val(data['data']['attributes']['king_playlist_protocol'].toLowerCase());
            _kingPlaylistTypeSelect.val(data['data']['attributes']['king_playlist_type'].toLowerCase());
            _kingEpgSourceSelect.val(data['data']['attributes']['king_epg_source'].toLowerCase());
            _kingEpgUrlInput.val(data['data']['attributes']['king_epg_url']);
            _smoothStreamsServiceSelect.val(data['data']['attributes']['smoothstreams_service'].toLowerCase());
            _smoothStreamsServerSelect.val(data['data']['attributes']['smoothstreams_server'].toLowerCase());
            _smoothStreamsUsernameInput.val(data['data']['attributes']['smoothstreams_username']);
            _smoothStreamsPasswordInput.val(data['data']['attributes']['smoothstreams_password']);
            _smoothStreamsPlaylistProtocolSelect.val(data['data']['attributes']['smoothstreams_playlist_protocol'].toLowerCase());
            _smoothStreamsPlaylistTypeSelect.val(data['data']['attributes']['smoothstreams_playlist_type'].toLowerCase());
            _smoothStreamsEpgSourceSelect.val(data['data']['attributes']['smoothstreams_epg_source'].toLowerCase());
            _smoothStreamsEpgUrlInput.val(data['data']['attributes']['smoothstreams_epg_url']);
            _universeUsernameInput.val(data['data']['attributes']['universe_username']);
            _universePasswordInput.val(data['data']['attributes']['universe_password']);
            _universePlaylistProtocolSelect.val(data['data']['attributes']['universe_playlist_protocol'].toLowerCase());
            _universePlaylistTypeSelect.val(data['data']['attributes']['universe_playlist_type'].toLowerCase());
            _universeEpgSourceSelect.val(data['data']['attributes']['universe_epg_source'].toLowerCase());
            _universeEpgUrlInput.val(data['data']['attributes']['universe_epg_url']);
            _vaderStreamsServerSelect.val(data['data']['attributes']['vaderstreams_server'].toLowerCase());
            _vaderStreamsUsernameInput.val(data['data']['attributes']['vaderstreams_username']);
            _vaderStreamsPasswordInput.val(data['data']['attributes']['vaderstreams_password']);
            _vaderStreamsPlaylistProtocolSelect.val(data['data']['attributes']['vaderstreams_playlist_protocol'].toLowerCase());
            _vaderStreamsPlaylistTypeSelect.val(data['data']['attributes']['vaderstreams_playlist_type'].toLowerCase());
            _vaderStreamsEpgSourceSelect.val(data['data']['attributes']['vaderstreams_epg_source'].toLowerCase());
            _vaderStreamsEpgUrlInput.val(data['data']['attributes']['vaderstreams_epg_url']);

            determineEpgUrlLabelInputVisibility();
            _disableResetAndUpdateButtons();
        });

        jqXHR.fail(function () {
            CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));

            // Set the color of the configurationAlertDiv
            _configurationAlertDiv.addClass('w3-red');

            // Set the color of the configurationSpan
            _configurationSpan.addClass('w3-red');

            // Set the text of the configurationHeader
            _configurationHeader.text('Error');

            // Set the text of the configurationMessageParagraph
            _configurationMessageParagraph.text('Failed to reset the configuration');

            if (jqXHR.status === 0) {
                // Set the text of the configurationReasonParagraph
                _configurationReasonParagraph.text('Check if IPTVProxy is up and running');
            }

            // Scroll to the bottom of the page
            $('html, body').animate({scrollTop: $(document).height()});

            // Show the configurationAlertDiv
            _configurationAlertDiv.show({duration: 1000});
        });
    };

    const toggleConfigurationDiv = function (idPrefix) {
        $('#' + idPrefix + 'Div').toggleClass('w3-hide');
    };

    const togglePasswordVisibility = function (event) {
        const eventTarget = $(event.target);

        let passwordInput = null;

        if (eventTarget.prop('id') === 'serverTogglePasswordSpan') {
            passwordInput = _serverPasswordInput;
        } else if (eventTarget.prop('id') === 'beastTogglePasswordSpan') {
            passwordInput = _beastPasswordInput;
        } else if (eventTarget.prop('id') === 'coolAsIceTogglePasswordSpan') {
            passwordInput = _coolAsIcePasswordInput;
        } else if (eventTarget.prop('id') === 'crystalClearTogglePasswordSpan') {
            passwordInput = _crystalClearPasswordInput;
        } else if (eventTarget.prop('id') === 'darkMediaTogglePasswordSpan') {
            passwordInput = _beastPasswordInput;
        } else if (eventTarget.prop('id') === 'helixTogglePasswordSpan') {
            passwordInput = _beastPasswordInput;
        } else if (eventTarget.prop('id') === 'infernoTogglePasswordSpan') {
            passwordInput = _infernoPasswordInput;
        } else if (eventTarget.prop('id') === 'kingTogglePasswordSpan') {
            passwordInput = _beastPasswordInput;
        } else if (eventTarget.prop('id') === 'smoothStreamsTogglePasswordSpan') {
            passwordInput = _smoothStreamsPasswordInput;
        } else if (eventTarget.prop('id') === 'universeTogglePasswordSpan') {
            passwordInput = _beastPasswordInput;
        } else if (eventTarget.prop('id') === 'vaderStreamsTogglePasswordSpan') {
            passwordInput = _vaderStreamsPasswordInput;
        }

        if (passwordInput) {
            if (passwordInput.prop('type') === 'text') {
                passwordInput.prop('type', 'password');
            } else {
                passwordInput.prop('type', 'text');
            }
        }

        eventTarget.toggleClass('fa-eye fa-eye-slash');
    };

    const updateConfiguration = function () {
        _clearConfigurationErrorMessages();
        CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));
        _disableResetAndUpdateButtons();

        const serverPasswordInputValue = _serverPasswordInput.val();
        const serverHttpPortInputValue = _serverHttpPortInput.val();
        const serverHttpsPortInputValue = _serverHttpsPortInput.val();
        const serverHostnameLoopbackInputValue = _serverHostnameLoopbackInput.val();
        const serverHostnamePrivateInputValue = _serverHostnamePrivateInput.val();
        const serverHostnamePublicInputValue = _serverHostnamePublicInput.val();
        const beastEnabledCheckboxChecked = _beastEnabledCheckbox.is(':checked');
        const beastUsernameInputValue = _beastUsernameInput.val();
        const beastPasswordInputValue = _beastPasswordInput.val();
        const beastPlaylistProtocolSelectValue = _beastPlaylistProtocolSelect.val();
        const beastPlaylistTypeSelectValue = _beastPlaylistTypeSelect.val();
        const beastEpgSourceSelectValue = _beastEpgSourceSelect.val();
        const beastEpgUrlInputValue = _beastEpgUrlInput.val();
        const coolAsIceEnabledCheckboxChecked = _coolAsIceEnabledCheckbox.is(':checked');
        const coolAsIceUsernameInputValue = _coolAsIceUsernameInput.val();
        const coolAsIcePasswordInputValue = _coolAsIcePasswordInput.val();
        const coolAsIcePlaylistProtocolSelectValue = _coolAsIcePlaylistProtocolSelect.val();
        const coolAsIcePlaylistTypeSelectValue = _coolAsIcePlaylistTypeSelect.val();
        const coolAsIceEpgSourceSelectValue = _coolAsIceEpgSourceSelect.val();
        const coolAsIceEpgUrlInputValue = _coolAsIceEpgUrlInput.val();
        const crystalClearEnabledCheckboxChecked = _crystalClearEnabledCheckbox.is(':checked');
        const crystalClearUsernameInputValue = _crystalClearUsernameInput.val();
        const crystalClearPasswordInputValue = _crystalClearPasswordInput.val();
        const crystalClearPlaylistProtocolSelectValue = _crystalClearPlaylistProtocolSelect.val();
        const crystalClearPlaylistTypeSelectValue = _crystalClearPlaylistTypeSelect.val();
        const crystalClearEpgSourceSelectValue = _crystalClearEpgSourceSelect.val();
        const crystalClearEpgUrlInputValue = _crystalClearEpgUrlInput.val();
        const darkMediaEnabledCheckboxChecked = _darkMediaEnabledCheckbox.is(':checked');
        const darkMediaUsernameInputValue = _darkMediaUsernameInput.val();
        const darkMediaPasswordInputValue = _darkMediaPasswordInput.val();
        const darkMediaPlaylistProtocolSelectValue = _darkMediaPlaylistProtocolSelect.val();
        const darkMediaPlaylistTypeSelectValue = _darkMediaPlaylistTypeSelect.val();
        const darkMediaEpgSourceSelectValue = _darkMediaEpgSourceSelect.val();
        const darkMediaEpgUrlInputValue = _darkMediaEpgUrlInput.val();
        const helixEnabledCheckboxChecked = _helixEnabledCheckbox.is(':checked');
        const helixUsernameInputValue = _helixUsernameInput.val();
        const helixPasswordInputValue = _helixPasswordInput.val();
        const helixPlaylistProtocolSelectValue = _helixPlaylistProtocolSelect.val();
        const helixPlaylistTypeSelectValue = _helixPlaylistTypeSelect.val();
        const helixEpgSourceSelectValue = _helixEpgSourceSelect.val();
        const helixEpgUrlInputValue = _helixEpgUrlInput.val();
        const infernoEnabledCheckboxChecked = _infernoEnabledCheckbox.is(':checked');
        const infernoUsernameInputValue = _infernoUsernameInput.val();
        const infernoPasswordInputValue = _infernoPasswordInput.val();
        const infernoPlaylistProtocolSelectValue = _infernoPlaylistProtocolSelect.val();
        const infernoPlaylistTypeSelectValue = _infernoPlaylistTypeSelect.val();
        const infernoEpgSourceSelectValue = _infernoEpgSourceSelect.val();
        const infernoEpgUrlInputValue = _infernoEpgUrlInput.val();
        const kingEnabledCheckboxChecked = _kingEnabledCheckbox.is(':checked');
        const kingUsernameInputValue = _kingUsernameInput.val();
        const kingPasswordInputValue = _kingPasswordInput.val();
        const kingPlaylistProtocolSelectValue = _kingPlaylistProtocolSelect.val();
        const kingPlaylistTypeSelectValue = _kingPlaylistTypeSelect.val();
        const kingEpgSourceSelectValue = _kingEpgSourceSelect.val();
        const kingEpgUrlInputValue = _kingEpgUrlInput.val();
        const smoothStreamsEnabledCheckboxChecked = _smoothStreamsEnabledCheckbox.is(':checked');
        const smoothStreamsServiceSelectValue = _smoothStreamsServiceSelect.val();
        const smoothStreamsServerSelectValue = _smoothStreamsServerSelect.val();
        const smoothStreamsUsernameInputValue = _smoothStreamsUsernameInput.val();
        const smoothStreamsPasswordInputValue = _smoothStreamsPasswordInput.val();
        const smoothStreamsPlaylistProtocolSelectValue = _smoothStreamsPlaylistProtocolSelect.val();
        const smoothStreamsPlaylistTypeSelectValue = _smoothStreamsPlaylistTypeSelect.val();
        const smoothStreamsEpgSourceSelectValue = _smoothStreamsEpgSourceSelect.val();
        const smoothStreamsEpgUrlInputValue = _smoothStreamsEpgUrlInput.val();
        const universeEnabledCheckboxChecked = _universeEnabledCheckbox.is(':checked');
        const universeUsernameInputValue = _universeUsernameInput.val();
        const universePasswordInputValue = _universePasswordInput.val();
        const universePlaylistProtocolSelectValue = _universePlaylistProtocolSelect.val();
        const universePlaylistTypeSelectValue = _universePlaylistTypeSelect.val();
        const universeEpgSourceSelectValue = _universeEpgSourceSelect.val();
        const universeEpgUrlInputValue = _universeEpgUrlInput.val();
        const vaderStreamsEnabledCheckboxChecked = _vaderStreamsEnabledCheckbox.is(':checked');
        const vaderStreamsServerSelectValue = _vaderStreamsServerSelect.val();
        const vaderStreamsUsernameInputValue = _vaderStreamsUsernameInput.val();
        const vaderStreamsPasswordInputValue = _vaderStreamsPasswordInput.val();
        const vaderStreamsPlaylistProtocolSelectValue = _vaderStreamsPlaylistProtocolSelect.val();
        const vaderStreamsPlaylistTypeSelectValue = _vaderStreamsPlaylistTypeSelect.val();
        const vaderStreamsEpgSourceSelectValue = _vaderStreamsEpgSourceSelect.val();
        const vaderStreamsEpgUrlInputValue = _vaderStreamsEpgUrlInput.val();

        const jqXHR = $.ajax({
                                 contentType: 'application/json',
                                 data: JSON.stringify({
                                                          'data':
                                                              {
                                                                  'type': 'configuration',
                                                                  'attributes': {
                                                                      'server_password': serverPasswordInputValue,
                                                                      'server_http_port': serverHttpPortInputValue,
                                                                      'server_https_port': serverHttpsPortInputValue,
                                                                      'server_hostname_loopback': serverHostnameLoopbackInputValue,
                                                                      'server_hostname_private': serverHostnamePrivateInputValue,
                                                                      'server_hostname_public': serverHostnamePublicInputValue,
                                                                      'beast_enabled': beastEnabledCheckboxChecked,
                                                                      'beast_username': beastUsernameInputValue,
                                                                      'beast_password': beastPasswordInputValue,
                                                                      'beast_playlist_protocol': beastPlaylistProtocolSelectValue,
                                                                      'beast_playlist_type': beastPlaylistTypeSelectValue,
                                                                      'beast_epg_source': beastEpgSourceSelectValue,
                                                                      'beast_epg_url': beastEpgUrlInputValue,
                                                                      'coolasice_enabled': coolAsIceEnabledCheckboxChecked,
                                                                      'coolasice_username': coolAsIceUsernameInputValue,
                                                                      'coolasice_password': coolAsIcePasswordInputValue,
                                                                      'coolasice_playlist_protocol': coolAsIcePlaylistProtocolSelectValue,
                                                                      'coolasice_playlist_type': coolAsIcePlaylistTypeSelectValue,
                                                                      'coolasice_epg_source': coolAsIceEpgSourceSelectValue,
                                                                      'coolasice_epg_url': coolAsIceEpgUrlInputValue,
                                                                      'crystalclear_enabled': crystalClearEnabledCheckboxChecked,
                                                                      'crystalclear_username': crystalClearUsernameInputValue,
                                                                      'crystalclear_password': crystalClearPasswordInputValue,
                                                                      'crystalclear_playlist_protocol': crystalClearPlaylistProtocolSelectValue,
                                                                      'crystalclear_playlist_type': crystalClearPlaylistTypeSelectValue,
                                                                      'crystalclear_epg_source': crystalClearEpgSourceSelectValue,
                                                                      'crystalclear_epg_url': crystalClearEpgUrlInputValue,
                                                                      'darkmedia_enabled': darkMediaEnabledCheckboxChecked,
                                                                      'darkmedia_username': darkMediaUsernameInputValue,
                                                                      'darkmedia_password': darkMediaPasswordInputValue,
                                                                      'darkmedia_playlist_protocol': darkMediaPlaylistProtocolSelectValue,
                                                                      'darkmedia_playlist_type': darkMediaPlaylistTypeSelectValue,
                                                                      'darkmedia_epg_source': darkMediaEpgSourceSelectValue,
                                                                      'darkmedia_epg_url': darkMediaEpgUrlInputValue,
                                                                      'helix_enabled': helixEnabledCheckboxChecked,
                                                                      'helix_username': helixUsernameInputValue,
                                                                      'helix_password': helixPasswordInputValue,
                                                                      'helix_playlist_protocol': helixPlaylistProtocolSelectValue,
                                                                      'helix_playlist_type': helixPlaylistTypeSelectValue,
                                                                      'helix_epg_source': helixEpgSourceSelectValue,
                                                                      'helix_epg_url': helixEpgUrlInputValue,
                                                                      'inferno_enabled': infernoEnabledCheckboxChecked,
                                                                      'inferno_username': infernoUsernameInputValue,
                                                                      'inferno_password': infernoPasswordInputValue,
                                                                      'inferno_playlist_protocol': infernoPlaylistProtocolSelectValue,
                                                                      'inferno_playlist_type': infernoPlaylistTypeSelectValue,
                                                                      'inferno_epg_source': infernoEpgSourceSelectValue,
                                                                      'inferno_epg_url': infernoEpgUrlInputValue,
                                                                      'king_enabled': kingEnabledCheckboxChecked,
                                                                      'king_username': kingUsernameInputValue,
                                                                      'king_password': kingPasswordInputValue,
                                                                      'king_playlist_protocol': kingPlaylistProtocolSelectValue,
                                                                      'king_playlist_type': kingPlaylistTypeSelectValue,
                                                                      'king_epg_source': kingEpgSourceSelectValue,
                                                                      'king_epg_url': kingEpgUrlInputValue,
                                                                      'smoothstreams_enabled': smoothStreamsEnabledCheckboxChecked,
                                                                      'smoothstreams_service': smoothStreamsServiceSelectValue,
                                                                      'smoothstreams_server': smoothStreamsServerSelectValue,
                                                                      'smoothstreams_username': smoothStreamsUsernameInputValue,
                                                                      'smoothstreams_password': smoothStreamsPasswordInputValue,
                                                                      'smoothstreams_playlist_protocol': smoothStreamsPlaylistProtocolSelectValue,
                                                                      'smoothstreams_playlist_type': smoothStreamsPlaylistTypeSelectValue,
                                                                      'smoothstreams_epg_source': smoothStreamsEpgSourceSelectValue,
                                                                      'smoothstreams_epg_url': smoothStreamsEpgUrlInputValue,
                                                                      'universe_enabled': universeEnabledCheckboxChecked,
                                                                      'universe_username': universeUsernameInputValue,
                                                                      'universe_password': universePasswordInputValue,
                                                                      'universe_playlist_protocol': universePlaylistProtocolSelectValue,
                                                                      'universe_playlist_type': universePlaylistTypeSelectValue,
                                                                      'universe_epg_source': universeEpgSourceSelectValue,
                                                                      'universe_epg_url': universeEpgUrlInputValue,
                                                                      'vaderstreams_enabled': vaderStreamsEnabledCheckboxChecked,
                                                                      'vaderstreams_server': vaderStreamsServerSelectValue,
                                                                      'vaderstreams_username': vaderStreamsUsernameInputValue,
                                                                      'vaderstreams_password': vaderStreamsPasswordInputValue,
                                                                      'vaderstreams_playlist_protocol': vaderStreamsPlaylistProtocolSelectValue,
                                                                      'vaderstreams_playlist_type': vaderStreamsPlaylistTypeSelectValue,
                                                                      'vaderstreams_epg_source': vaderStreamsEpgSourceSelectValue,
                                                                      'vaderstreams_epg_url': vaderStreamsEpgUrlInputValue
                                                                  },
                                                              }
                                                      }, function (key, value) {
                                     return (value == null) ? '' : value
                                 }),
                                 dataType: 'json',
                                 headers: {'Authorization': 'Basic {{ authorization_basic_password }}'},
                                 method: 'PATCH',
                                 timeout: 5000,
                                 url: '/configuration'
                             });

        jqXHR.done(function () {
            _serializeConfigurationForm();

            _clearConfigurationErrorMessages();
            CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));
            _disableResetAndUpdateButtons();

            // Set the color of the configurationAlertDiv
            _configurationAlertDiv.addClass('w3-green');

            // Set the color of the configurationSpan
            _configurationSpan.addClass('w3-green');

            // Set the text of the configurationHeader
            _configurationHeader.text('Success');

            // Set the text of the configurationMessageParagraph
            _configurationMessageParagraph.text('Successfully updated configuration');

            // Show the configurationAlertDiv
            _configurationAlertDiv.show({duration: 1000});

            // Scroll to the bottom of the page
            $('html, body').animate({scrollTop: $(document).height()});

            setTimeout(function () {
                CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));
            }, 30000);
        });

        jqXHR.fail(function (jqXHR) {
            _clearConfigurationErrorMessages();
            CommonModule.resetAlertDiv(_configurationAlertDiv.prop('id'));

            // Set the color of the configurationAlertDiv
            _configurationAlertDiv.addClass('w3-red');

            // Set the color of the configurationSpan
            _configurationSpan.addClass('w3-red');

            // Set the text of the configurationHeader
            _configurationHeader.text('Error');

            // Set the text of the configurationMessageParagraph
            _configurationMessageParagraph.text('Failed to update configuration');

            if (jqXHR.status === 0) {
                // Set the text of the configurationReasonParagraph
                _configurationReasonParagraph.text('Check if IPTVProxy is up and running');
            } else if (jqXHR.status === HttpCodes.BAD_REQUEST) {
                // Set the text of the configurationReasonParagraph
                _configurationReasonParagraph.text('Encountered unexpected error');
            } else if (jqXHR.status === HttpCodes.UNPROCESSABLE_ENTITY) {
                const responseJson = JSON.parse(jqXHR.responseText);

                for (let i = 0; i < responseJson['errors'].length; i++) {
                    $('[id^="' + responseJson['errors'][i]['field'] + '"]')
                        .not('[id$="ErrorSpan"]')
                        .addClass('w3-border-red w3-bottombar w3-leftbar w3-rightbar w3-topbar');
                    $('[id^="' + responseJson['errors'][i]['field'] + '"][id$="ErrorSpan"]')
                        .html(responseJson['errors'][i]['user_message'].replace('\n', '<br />'));
                }
            }

            // Show the configurationAlertDiv
            _configurationAlertDiv.show({duration: 1000});

            // Scroll to the bottom of the page
            $('html, body').animate({scrollTop: $(document).height()});

            _enableResetAndUpdateButtons();
        });
    };

    return {
        determineEpgUrlLabelInputVisibility: determineEpgUrlLabelInputVisibility,
        determineProviderConfigurationInputsState: determineProviderConfigurationInputsState,
        determineResetAndUpdateButtonsState: determineResetAndUpdateButtonsState,
        init: init,
        resetConfiguration: resetConfiguration,
        toggleConfigurationDiv: toggleConfigurationDiv,
        togglePasswordVisibility: togglePasswordVisibility,
        updateConfiguration: updateConfiguration
    }
})();

const SettingsModule = (function () {
    let _dayImages = null;
    let _contentDiv = null;
    let _guideSortBySelect = null;
    let _guideSortOrderSelect = null;
    let _lastSelectedGuideNumberOfDays = null;
    let _lastSelectedGuideSortBy = null;
    let _lastSelectedGuideSortOrder = null;
    let _lastSelectedStreamingProtocol = null;
    let _loadingDiv = null;
    let _loadingHeader = null;
    let _protocolImages = null;
    let _selectedGuideNumberOfDays = null;
    let _selectedGuideSortBy = null;
    let _selectedGuideSortOrder = null;
    let _selectedStreamingProtocol = null;
    let _settingsApplyButton = null;
    let _settingsButtons = null;
    let _settingsDiv = null;
    let _settingsDivs = null;
    let _settingsResetButton = null;

    const _disableResetAndApplyButtons = function () {
        // Disable the settingsResetButton
        _settingsResetButton.addClass('w3-disabled');

        // Disable the settingsApplyButton
        _settingsApplyButton.addClass('w3-disabled');
    };

    const _enableResetAndApplyButtons = function () {
        // Enable the settingsResetButton
        _settingsResetButton.removeClass('w3-disabled');

        // Enable the settingsApplyButton
        _settingsApplyButton.removeClass('w3-disabled');
    };

    const _numberOfDaysSelectedChangeHandler = function () {
        const settings_cookie_expires = Cookies.get('settings_cookie_expires')
                                               .replace(/\\(\d{3})/g, function (match, octal) {
                                                   return String.fromCharCode(parseInt(octal, 8));
                                               });

        if (settings_cookie_expires) {
            const expires = moment(settings_cookie_expires).utc().toDate();

            Cookies.set('guide_number_of_days', _selectedGuideNumberOfDays, {
                expires: expires,
                path: '/index.html'
            });
        }

        _loadingHeader.text('Refreshing guide from ' +
                            _lastSelectedGuideNumberOfDays +
                            ' day' +
                            (_lastSelectedGuideNumberOfDays === '1' ? '' : 's') +
                            ' to ' +
                            _selectedGuideNumberOfDays +
                            ' day' +
                            (_selectedGuideNumberOfDays === '1' ? '' : 's'));

        _loadingDiv.show();

        const jqXHR = $.ajax({
                                 dataType: 'html',
                                 method: 'GET',
                                 timeout: 0,
                                 url: '/index.html?refresh_epg=1'
                             });

        jqXHR.done(function (data) {
            if (data.startsWith('    <div')) {
                const guideDiv = $('#guideDiv');

                guideDiv.remove();

                _contentDiv.prepend(data);

                ResizeModule.resizeContentDiv();
                ResizeModule.resizeGuideAndVideoDivs();

                _lastSelectedGuideNumberOfDays = _selectedGuideNumberOfDays;

                GuideModule.sortChannels(SettingsModule.getSelectedGuideSortBy(),
                                         SettingsModule.getSelectedGuideSortOrder());

                _loadingDiv.hide();
            } else {
                const headInnerHtml = data.substring(data.indexOf('<head>') + 6, data.indexOf('</head>'));
                const bodyInnerHtml = data.substring(data.indexOf('<body>') + 6, data.indexOf('</body>'));

                $('head').html(headInnerHtml);
                $('body').html(bodyInnerHtml);

                _loadingDiv.hide();
            }
        });

        jqXHR.fail(function () {
            _loadingDiv.hide();
        });
    };

    const _protocolSelectedChangeHandler = function () {
        const settings_cookie_expires = Cookies.get('settings_cookie_expires')
                                               .replace(/\\(\d{3})/g, function (match, octal) {
                                                   return String.fromCharCode(parseInt(octal, 8));
                                               });

        if (settings_cookie_expires) {
            const expires = moment(settings_cookie_expires).utc().toDate();

            Cookies.set('streaming_protocol', _selectedStreamingProtocol, {
                expires: expires,
                path: '/index.html'
            });
        }

        if (VideoPlayerModule.isVideoPlaying()) {
            const lastPlayedVideoSourceType = VideoPlayerModule.getLastPlayedVideoSourceType();

            if (lastPlayedVideoSourceType === 'live') {
                VideoPlayerModule.pauseVideo();

                VideoPlayerModule.playVideo(lastPlayedVideoSourceType,
                                            VideoPlayerModule.getLastPlayedVideoSources(),
                                            VideoPlayerModule.getLastPlayedVideoDetails());
            }
        }

        _lastSelectedStreamingProtocol = _selectedStreamingProtocol;
    };

    const applySettings = function () {
        closeSettingsDiv();

        if (_selectedGuideNumberOfDays !== _lastSelectedGuideNumberOfDays) {
            _numberOfDaysSelectedChangeHandler();
        }

        _selectedGuideSortBy = parseInt(_guideSortBySelect.val());
        _selectedGuideSortOrder = parseInt(_guideSortOrderSelect.val());

        if ((_selectedGuideSortBy !== _lastSelectedGuideSortBy) ||
            (_selectedGuideSortOrder !== _lastSelectedGuideSortOrder)) {
            GuideModule.sortChannels(_selectedGuideSortBy, _selectedGuideSortOrder);

            _lastSelectedGuideSortBy = _selectedGuideSortBy;
            _lastSelectedGuideSortOrder = _selectedGuideSortOrder;

            const settings_cookie_expires = Cookies.get('settings_cookie_expires')
                                                   .replace(/\\(\d{3})/g, function (match, octal) {
                                                       return String.fromCharCode(parseInt(octal, 8));
                                                   });

            if (settings_cookie_expires) {
                const expires = moment(settings_cookie_expires).utc().toDate();

                Cookies.set('guide_sort_by', _selectedGuideSortBy, {
                    expires: expires,
                    path: '/index.html'
                });

                Cookies.set('guide_sort_order', _selectedGuideSortOrder, {
                    expires: expires,
                    path: '/index.html'
                });
            }
        }

        if (_selectedStreamingProtocol !== _lastSelectedStreamingProtocol) {
            _protocolSelectedChangeHandler();
        }

        _disableResetAndApplyButtons();
    };

    const closeSettingsDiv = function () {
        _settingsDiv.hide();
    };

    const determineResetAndApplyButtonsState = function () {
        if ((_selectedGuideNumberOfDays !== _lastSelectedGuideNumberOfDays) ||
            (parseInt(_guideSortBySelect.val()) !== _lastSelectedGuideSortBy) ||
            (parseInt(_guideSortOrderSelect.val()) !== _lastSelectedGuideSortOrder) ||
            (_selectedStreamingProtocol !== _lastSelectedStreamingProtocol)) {
            _enableResetAndApplyButtons();
        } else {
            _disableResetAndApplyButtons();
        }
    };

    const getSelectedGuideSortBy = function () {
        return _selectedGuideSortBy;
    };

    const getSelectedGuideSortOrder = function () {
        return _selectedGuideSortOrder;
    };

    const getSelectedStreamingProtocol = function () {
        return _selectedStreamingProtocol;
    };

    const init = function () {
        _dayImages = $('#1Image, #2Image, #3Image, #4Image, #5Image');
        _contentDiv = $('#contentDiv');
        _guideSortBySelect = $('#guideSortBySelect');
        _guideSortOrderSelect = $('#guideSortOrderSelect');
        _lastSelectedGuideNumberOfDays = '{{ last_selected_guide_number_of_days }}';
        _lastSelectedGuideSortBy =
            'guide_sort_by' in
            Cookies.get() ? parseInt(Cookies.get('guide_sort_by')) : GuideSortCriteria.CHANNEL_NUMBER;
        _lastSelectedGuideSortOrder =
            'guide_sort_order' in
            Cookies.get() ? parseInt(Cookies.get('guide_sort_order')) : SortOrder.ASCENDING;
        _lastSelectedStreamingProtocol = '{{ last_selected_streaming_protocol }}';
        _loadingDiv = $('#loadingDiv');
        _loadingHeader = $('#loadingHeader');
        _protocolImages = $('#hlsImage, #rtmpImage');
        _selectedGuideNumberOfDays = '{{ last_selected_guide_number_of_days }}';
        _selectedGuideSortBy =
            'guide_sort_by' in
            Cookies.get() ? parseInt(Cookies.get('guide_sort_by')) : GuideSortCriteria.CHANNEL_NUMBER;
        _selectedGuideSortOrder =
            'guide_sort_order' in
            Cookies.get() ? parseInt(Cookies.get('guide_sort_order')) : SortOrder.ASCENDING;
        _selectedStreamingProtocol = '{{ last_selected_streaming_protocol }}';
        _settingsApplyButton = $('#settingsApplyButton');
        _settingsButtons = $('#guideSettingsButton, #streamingSettingsButton');
        _settingsDiv = $('#settingsDiv');
        _settingsDivs = $('#guideSettingsDiv, #streamingSettingsDiv');
        _settingsResetButton = $('#settingsResetButton');
    };

    const openSettingsDiv = function () {
        resetSettings();
        openSettingsTab('guide');

        _settingsDiv.show();
    };

    const openSettingsTab = function (idPrefix) {
        _settingsDivs.not('#' + idPrefix + 'SettingsDiv').hide({duration: 500});

        _settingsButtons.not('#' + idPrefix + 'Button').removeClass('w3-dark-grey');

        $('#' + idPrefix + 'SettingsButton').addClass('w3-dark-grey');
        $('#' + idPrefix + 'SettingsDiv').show();

        if (idPrefix === 'guide') {
            ResizeModule.resizeNumberImages();
        } else if (idPrefix === 'streaming') {
            ResizeModule.resizeProtocolImages();
        }
    };

    const resetSettings = function () {
        if (_selectedGuideNumberOfDays !== _lastSelectedGuideNumberOfDays) {
            updateNumberOfDaysImages(_lastSelectedGuideNumberOfDays);
        }

        if (parseInt(_guideSortBySelect.val()) !== _lastSelectedGuideSortBy) {
            _guideSortBySelect.val(_lastSelectedGuideSortBy)
        }

        if (parseInt(_guideSortOrderSelect.val()) !== _lastSelectedGuideSortOrder) {
            _guideSortOrderSelect.val(_lastSelectedGuideSortOrder)
        }

        if (_selectedStreamingProtocol !== _lastSelectedStreamingProtocol) {
            updateProtocolImages(_lastSelectedStreamingProtocol);
        }

        _disableResetAndApplyButtons();
    };

    const updateNumberOfDaysImages = function (selectedNumberOfDays) {
        _selectedGuideNumberOfDays = selectedNumberOfDays;

        const selectedImage = $('#' + selectedNumberOfDays + 'Image');
        const unselectedImages = _dayImages.not('#' + selectedImage.prop('id'));

        selectedImage.removeClass('w3-opacity-max');
        selectedImage.addClass('w3-border-blue w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        selectedImage.removeAttr('onclick');
        selectedImage.css({
                              'cursor': '',
                              'padding': '8px'
                          });

        unselectedImages.removeClass('w3-border-blue w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        unselectedImages.addClass('w3-opacity-max');
        unselectedImages.each(function () {
            $(this)
                .attr('onclick', 'SettingsModule.updateNumberOfDaysImages(\'' +
                                 $(this).prop('id').replace('Image', '') +
                                 '\')');
        });
        unselectedImages.css({
                                 'cursor': 'pointer',
                                 'padding': '14px'
                             });

        determineResetAndApplyButtonsState();
    };

    const updateProtocolImages = function (selectedProtocol) {
        _selectedStreamingProtocol = selectedProtocol;

        const selectedImage = $('#' + selectedProtocol + 'Image');
        const unselectedImage = _protocolImages.not('#' + selectedImage.prop('id'));

        selectedImage.removeClass('w3-grayscale-max');
        selectedImage.addClass('w3-border-blue w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        selectedImage.removeAttr('onclick');
        selectedImage.css({
                              'cursor': '',
                              'padding': '8px'
                          });

        unselectedImage.removeClass('w3-border-blue w3-bottombar w3-leftbar w3-rightbar w3-topbar');
        unselectedImage.addClass('w3-grayscale-max');
        unselectedImage.attr('onclick', 'SettingsModule.updateProtocolImages(\'' +
                                        unselectedImage.prop('id').replace('Image', '') +
                                        '\')');
        unselectedImage.css({
                                'cursor': 'pointer',
                                'padding': '14px'
                            });

        determineResetAndApplyButtonsState();
    };

    return {
        applySettings: applySettings,
        closeSettingsDiv: closeSettingsDiv,
        determineResetAndApplyButtonsState: determineResetAndApplyButtonsState,
        getSelectedGuideSortBy: getSelectedGuideSortBy,
        getSelectedGuideSortOrder: getSelectedGuideSortOrder,
        getSelectedStreamingProtocol: getSelectedStreamingProtocol,
        init: init,
        openSettingsDiv: openSettingsDiv,
        openSettingsTab: openSettingsTab,
        resetSettings: resetSettings,
        updateNumberOfDaysImages: updateNumberOfDaysImages,
        updateProtocolImages: updateProtocolImages
    };
})();