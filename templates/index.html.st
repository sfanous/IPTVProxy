<!DOCTYPE html>
<html lang="en"
      style="overflow: hidden;">
<head>
    <link crossorigin="anonymous"
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
          integrity="sha256-eZrrJcwDc/3uDhsdt61sL2oOBY362qM3lon1gyExkL0="
          rel="stylesheet"/>
    <link crossorigin="anonymous"
          href="https://cdnjs.cloudflare.com/ajax/libs/video.js/6.8.0/video-js.min.css"
          integrity="sha256-eXoB2lxpqIgd9VUhTEJfMF3F9X7W7SNNeo1eZzZ5dkc="
          rel="stylesheet"/>
    <link crossorigin="anonymous"
          href="https://cdnjs.cloudflare.com/ajax/libs/videojs-overlay/1.1.4/videojs-overlay.css"
          integrity="sha256-KflMcBmUiYyVi/Fgy2IqwyV9lKRFa0IXE/FkaRM2R7s="
          rel="stylesheet"/>
    <link href="https://www.w3schools.com/w3css/4/w3.css"
          rel="stylesheet"/>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1"
          name="viewport">
    <script crossorigin="anonymous"
            integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
            src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-N9uoe2+n6MvVDA1QdroEt3vRgtxfSKFM63qxRqVXfLE="
            src="https://cdnjs.cloudflare.com/ajax/libs/jquery.tablesorter/2.30.1/js/jquery.tablesorter.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-9Nt2r+tJnSd2A2CRUvnjgsD+ES1ExvjbjBNqidm9doI="
            src="https://cdnjs.cloudflare.com/ajax/libs/js-cookie/2.2.0/js.cookie.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-lSUsmgZjp8RLeiE79c2BwjMtoxiPTpaFMROQe6NsnBU="
            src="https://cdn.jsdelivr.net/npm/m3u8-parser@4.2.0/dist/m3u8-parser.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-L3S3EDEk31HcLA5C6T2ovHvOcD80+fgqaCDt2BAi92o="
            src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.22.1/moment.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-rHiL88E97qpnkdaA4JtGNOXVaZ96xvqGa5ujMo9Ji4s="
            src="https://cdnjs.cloudflare.com/ajax/libs/video.js/6.8.0/video.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-ngHSRzCW6euvtJPYDc6HnWd9UvS7VxXfOcRt5Kt0ZrA="
            src="https://cdnjs.cloudflare.com/ajax/libs/videojs-contrib-hls/5.14.1/videojs-contrib-hls.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-kPZ6+J+WmX3iS2kiXHZGEbG8qcpLnSEp5GJsoSgJelw="
            src="https://cdnjs.cloudflare.com/ajax/libs/videojs-flash/2.1.0/videojs-flash.min.js"></script>
    <script crossorigin="anonymous"
            integrity="sha256-X50EiI4SdUvAgGOYcpOzWkMcsX8vTOdfuDV+XccNHYA="
            src="https://cdnjs.cloudflare.com/ajax/libs/videojs-overlay/1.1.4/videojs-overlay.min.js"></script>
    <script>
${iptv_proxy_script}
    </script>
    <style>
        th.tablesorter-header {
            background-image: url(data:image/gif;base64,R0lGODlhFQAJAIAAACMtMP///yH5BAEAAAEALAAAAAAVAAkAAAIXjI+AywnaYnhUMoqt3gZXPmVg94yJVQAAOw==);
            background-repeat: no-repeat;
            background-position: center right;
            cursor: pointer;
        }

        th.tablesorter-headerDesc {
            background-image: url(data:image/gif;base64,R0lGODlhFQAEAIAAACMtMP///yH5BAEAAAEALAAAAAAVAAQAAAINjI8Bya2wnINUMopZAQA7);
        }

        th.tablesorter-headerAsc {
            background-image: url(data:image/gif;base64,R0lGODlhFQAEAIAAACMtMP///yH5BAEAAAEALAAAAAAVAAQAAAINjB+gC+jP2ptn0WskLQA7);
        }

        th.sorter-false {
            background-image: none;
            cursor: default;
            padding: 4px;
        }
    </style>
    <title>IPTVProxy ${iptv_proxy_version}</title>
</head>
<body>
<div class="w3-top"
     id="navigationBarDiv"
     style="padding: 0.01em 16px;">
    <div class="w3-bar w3-light-grey"
         id="navigationBarButtonsDiv"
         style="padding: 1px;">
        <button class="w3-bar-item w3-button w3-dark-grey w3-mobile"
                id="guideButton"
                onclick="MenuModule.openTab('guide')">Guide
        </button>
        <button class="w3-bar-item w3-button w3-mobile"
                id="recordingsButton"
                onclick="MenuModule.openTab('recordings')">Recordings
        </button>
        <button class="w3-bar-item w3-button w3-mobile"
                id="configurationButton"
                onclick="MenuModule.openTab('configuration')">Configuration
        </button>
        <button class="w3-bar-item w3-button w3-mobile"
                id="monitorButton"
                onclick="MenuModule.openTab('monitor')">Monitor
        </button>
        <button class="w3-bar-item w3-button w3-mobile"
                id="aboutButton"
                onclick="MenuModule.openTab('about')">About
        </button>
        <button class="w3-button w3-right w3-mobile"
                id="settingsButton"
                onclick="SettingsModule.openSettingsDiv()">
            <span class="fa fa-cog fa-lg"></span>
        </button>
        <form action=""
              autocomplete="off"
              novalidate="novalidate">
            <input class="w3-bar-item w3-input w3-right"
                   id="searchGuideInputText"
                   placeholder="Search..."
                   oninput="GuideModule.searchGuide()"
                   type="text"/>
            <span class="w3-bar-item w3-right"
                  id="separatorSpan"
                  style="display: inline-block; padding: 4px;"></span>
            <select class="w3-bar-item w3-right w3-select"
                    id="guideGroupSelect"
                    name="guideGroupSelect"
                    oninput="GuideModule.updateGroup()"
                    title="">
                <option disabled="disabled"
                        selected="selected"
                        value="">Choose your option
                </option>
${guide_group_select_options}
            </select>
        </form>
    </div>
</div>
<div id="settingsDiv" class="w3-modal">
            <div class="w3-animate-zoom w3-card-4 w3-modal-content"
                 style="height: auto">
                <header class="w3-container w3-black">
                    <span class="w3-btn w3-display-topright"
                          onclick="SettingsModule.closeSettingsDiv()">&times;</span>
                    <h2>Settings</h2>
                </header>
                <div class="w3-bar w3-light-grey">
                    <button class="w3-bar-item w3-button w3-dark-grey"
                            id="guideSettingsButton"
                            onclick="SettingsModule.openSettingsTab('guide')">Guide
                    </button>
                    <button class="w3-bar-item w3-button"
                            id="streamingSettingsButton"
                            onclick="SettingsModule.openSettingsTab('streaming')">Streaming
                    </button>
                </div>
                <div class="w3-center w3-padding"
                     id="guideSettingsDiv">
                    <h2>Days</h2>
                    <img class="${_1_image_class}"
                         id="1Image"
                         ${_1_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933333%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg31%22%0A%20%20%20sodipodi%3Adocname%3D%221.svg%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs25%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%221.4%22%0A%20%20%20%20%20inkscape%3Acx%3D%22208.14286%22%0A%20%20%20%20%20inkscape%3Acy%3D%2245.714286%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata28%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06667%29%22%3E%0A%20%20%20%20%3Ctext%0A%20%20%20%20%20%20%20xml%3Aspace%3D%22preserve%22%0A%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bline-height%3A125%25%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bletter-spacing%3A0px%3Bword-spacing%3A0px%3Bfill%3A%23000000%3Bfill-opacity%3A1%3Bstroke%3Anone%3Bstroke-width%3A0.26458332px%3Bstroke-linecap%3Abutt%3Bstroke-linejoin%3Amiter%3Bstroke-opacity%3A1%22%0A%20%20%20%20%20%20%20x%3D%220.055121496%22%0A%20%20%20%20%20%20%20y%3D%22296.76297%22%0A%20%20%20%20%20%20%20id%3D%22text39%22%3E%3Ctspan%0A%20%20%20%20%20%20%20%20%20sodipodi%3Arole%3D%22line%22%0A%20%20%20%20%20%20%20%20%20id%3D%22tspan37%22%0A%20%20%20%20%20%20%20%20%20x%3D%220.055121496%22%0A%20%20%20%20%20%20%20%20%20y%3D%22296.76297%22%0A%20%20%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bstroke-width%3A0.26458332px%22%3E1%3C%2Ftspan%3E%3C%2Ftext%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${_1_image_style}"/>
                    <span style="display: inline-block; width: 16px;"></span>
                    <img class="${_2_image_class}"
                         id="2Image"
                         ${_2_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933333%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg31%22%0A%20%20%20sodipodi%3Adocname%3D%222.svg%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs25%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%221.4%22%0A%20%20%20%20%20inkscape%3Acx%3D%22208.14286%22%0A%20%20%20%20%20inkscape%3Acy%3D%2245.714286%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata28%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06667%29%22%3E%0A%20%20%20%20%3Ctext%0A%20%20%20%20%20%20%20xml%3Aspace%3D%22preserve%22%0A%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bline-height%3A125%25%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bletter-spacing%3A0px%3Bword-spacing%3A0px%3Bfill%3A%23000000%3Bfill-opacity%3A1%3Bstroke%3Anone%3Bstroke-width%3A0.26458332px%3Bstroke-linecap%3Abutt%3Bstroke-linejoin%3Amiter%3Bstroke-opacity%3A1%22%0A%20%20%20%20%20%20%20x%3D%22-0.016536491%22%0A%20%20%20%20%20%20%20y%3D%22296.90079%22%0A%20%20%20%20%20%20%20id%3D%22text43%22%3E%3Ctspan%0A%20%20%20%20%20%20%20%20%20sodipodi%3Arole%3D%22line%22%0A%20%20%20%20%20%20%20%20%20id%3D%22tspan41%22%0A%20%20%20%20%20%20%20%20%20x%3D%22-0.016536491%22%0A%20%20%20%20%20%20%20%20%20y%3D%22296.90079%22%0A%20%20%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bstroke-width%3A0.26458332px%22%3E2%3C%2Ftspan%3E%3C%2Ftext%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${_2_image_style}"/>
                    <span style="display: inline-block; width: 16px;"></span>
                    <img class="${_3_image_class}"
                         id="3Image"
                         ${_3_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933334%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg3755%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%0A%20%20%20sodipodi%3Adocname%3D%223.svg%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs3749%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%220.35%22%0A%20%20%20%20%20inkscape%3Acx%3D%22400%22%0A%20%20%20%20%20inkscape%3Acy%3D%22560%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata3752%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06665%29%22%3E%0A%20%20%20%20%3Ctext%0A%20%20%20%20%20%20%20xml%3Aspace%3D%22preserve%22%0A%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.46825981px%3Bline-height%3A125%25%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bletter-spacing%3A0px%3Bword-spacing%3A0px%3Bfill%3A%23000000%3Bfill-opacity%3A1%3Bstroke%3Anone%3Bstroke-width%3A0.26329988px%3Bstroke-linecap%3Abutt%3Bstroke-linejoin%3Amiter%3Bstroke-opacity%3A1%22%0A%20%20%20%20%20%20%20x%3D%220.44437596%22%0A%20%20%20%20%20%20%20y%3D%22298.10553%22%0A%20%20%20%20%20%20%20id%3D%22text3759%22%0A%20%20%20%20%20%20%20transform%3D%22scale%281.0048675%2C0.99515607%29%22%3E%3Ctspan%0A%20%20%20%20%20%20%20%20%20sodipodi%3Arole%3D%22line%22%0A%20%20%20%20%20%20%20%20%20id%3D%22tspan3757%22%0A%20%20%20%20%20%20%20%20%20x%3D%220.44437596%22%0A%20%20%20%20%20%20%20%20%20y%3D%22298.10553%22%0A%20%20%20%20%20%20%20%20%20style%3D%22font-size%3A22.46825981px%3Bstroke-width%3A0.26329988px%22%3E3%3C%2Ftspan%3E%3C%2Ftext%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${_3_image_style}"/>
                    <span style="display: inline-block; width: 16px;"></span>
                    <img class="${_4_image_class}"
                         id="4Image"
                         ${_4_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933334%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg3781%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%0A%20%20%20sodipodi%3Adocname%3D%224.svg%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs3775%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%220.35%22%0A%20%20%20%20%20inkscape%3Acx%3D%22400%22%0A%20%20%20%20%20inkscape%3Acy%3D%22560%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata3778%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06665%29%22%3E%0A%20%20%20%20%3Ctext%0A%20%20%20%20%20%20%20xml%3Aspace%3D%22preserve%22%0A%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bline-height%3A125%25%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bletter-spacing%3A0px%3Bword-spacing%3A0px%3Bfill%3A%23000000%3Bfill-opacity%3A1%3Bstroke%3Anone%3Bstroke-width%3A0.26458332px%3Bstroke-linecap%3Abutt%3Bstroke-linejoin%3Amiter%3Bstroke-opacity%3A1%22%0A%20%20%20%20%20%20%20x%3D%220.42443573%22%0A%20%20%20%20%20%20%20y%3D%22296.71887%22%0A%20%20%20%20%20%20%20id%3D%22text3785%22%3E%3Ctspan%0A%20%20%20%20%20%20%20%20%20sodipodi%3Arole%3D%22line%22%0A%20%20%20%20%20%20%20%20%20id%3D%22tspan3783%22%0A%20%20%20%20%20%20%20%20%20x%3D%220.42443573%22%0A%20%20%20%20%20%20%20%20%20y%3D%22296.71887%22%0A%20%20%20%20%20%20%20%20%20style%3D%22font-size%3A22.57777786px%3Bstroke-width%3A0.26458332px%22%3E4%3C%2Ftspan%3E%3C%2Ftext%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${_4_image_style}"/>
                    <span style="display: inline-block; width: 16px;"></span>
                    <img class="${_5_image_class}"
                         id="5Image"
                         ${_5_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933333%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg3793%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%0A%20%20%20sodipodi%3Adocname%3D%225.svg%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs3787%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%220.35%22%0A%20%20%20%20%20inkscape%3Acx%3D%22400%22%0A%20%20%20%20%20inkscape%3Acy%3D%22560%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata3790%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06667%29%22%3E%0A%20%20%20%20%3Ctext%0A%20%20%20%20%20%20%20xml%3Aspace%3D%22preserve%22%0A%20%20%20%20%20%20%20style%3D%22font-style%3Anormal%3Bfont-variant%3Anormal%3Bfont-weight%3Abold%3Bfont-stretch%3Anormal%3Bfont-size%3A22.57777786px%3Bline-height%3A125%25%3Bfont-family%3AVerdana%3B-inkscape-font-specification%3A%27Verdana%20Bold%27%3Bletter-spacing%3A0px%3Bword-spacing%3A0px%3Bfill%3A%23000000%3Bfill-opacity%3A1%3Bstroke%3Anone%3Bstroke-width%3A0.26458332px%3Bstroke-linecap%3Abutt%3Bstroke-linejoin%3Amiter%3Bstroke-opacity%3A1%22%0A%20%20%20%20%20%20%20x%3D%220.27560762%22%0A%20%20%20%20%20%20%20y%3D%22296.57007%22%0A%20%20%20%20%20%20%20id%3D%22text3797%22%3E%3Ctspan%0A%20%20%20%20%20%20%20%20%20sodipodi%3Arole%3D%22line%22%0A%20%20%20%20%20%20%20%20%20id%3D%22tspan3795%22%0A%20%20%20%20%20%20%20%20%20x%3D%220.27560762%22%0A%20%20%20%20%20%20%20%20%20y%3D%22296.57007%22%0A%20%20%20%20%20%20%20%20%20style%3D%22stroke-width%3A0.26458332px%22%3E5%3C%2Ftspan%3E%3C%2Ftext%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${_5_image_style}"/>
                    <br/>
                    <h2>Sorting</h2>
                    <form action=""
                          autocomplete="off"
                          id="guideSortingForm"
                          novalidate="novalidate">
                        <div class="w3-row-padding">
                            <div class="w3-half">
                                <label for="guideSortBySelect">Sort by:</label>
                                <select class="w3-border w3-select"
                                        id="guideSortBySelect"
                                        name="guideSortBySelect"
                                        oninput="SettingsModule.determineResetAndApplyButtonsState()">
                                    <option disabled="disabled"
                                            value="">Choose your option
                                    </option>
                                    <option value="0">Channel Name</option>
                                    <option value="1">Channel Number</option>
                                </select>
                            </div>
                             <div class="w3-half">
                                 <label for="guideSortOrderSelect">Sort order:</label>
                                <select class="w3-border w3-select"
                                        id="guideSortOrderSelect"
                                        name="guideSortOrderSelect"
                                        oninput="SettingsModule.determineResetAndApplyButtonsState()">
                                    <option disabled="disabled"
                                            value="">Choose your option
                                    </option>
                                    <option value="0">Ascending</option>
                                    <option value="1">Descending</option>
                                </select>
                             </div>
                        </div>
                    </form>
                </div>
                <div class="w3-center w3-padding"
                     id="streamingSettingsDiv"
                     style="display: none;">
                    <h2>Protocol</h2>
                    <img class="${hls_image_class}"
                         id="hlsImage"
                         ${hls_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933334%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg257%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%0A%20%20%20sodipodi%3Adocname%3D%22HTML5.svg%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs251%22%20%2F%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%221%22%0A%20%20%20%20%20inkscape%3Acx%3D%22317%22%0A%20%20%20%20%20inkscape%3Acy%3D%220%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata254%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06665%29%22%3E%0A%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20id%3D%22g284%22%0A%20%20%20%20%20%20%20transform%3D%22matrix%280.03307292%2C0%2C0%2C0.03307292%2C-8.5333333e-7%2C280.06665%29%22%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20id%3D%22path261%22%0A%20%20%20%20%20%20%20%20%20d%3D%22m%20108.4%2C0%20h%2023%20v%2022.8%20h%2021.2%20V%200%20h%2023%20v%2069%20h%20-23%20V%2046%20h%20-21%20V%2069%20H%20108.4%20M%20206%2C23%20H%20185.7%20V%200%20h%2063.7%20V%2023%20H%20229%20V%2069%20H%20206%20M%20259.5%2C0%20h%2024.1%20L%20298.4%2C24.3%20313.2%2C0%20h%2024.1%20v%2069%20h%20-23%20V%2034.8%20L%20298.2%2C59.6%20282.1%2C34.8%20V%2069%20H%20259.5%20M%20348.7%2C0%20h%2023%20v%2046.2%20h%2032.6%20V%2069%20h%20-55.6%22%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%20%2F%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20id%3D%22path263%22%0A%20%20%20%20%20%20%20%20%20d%3D%22M%20107.6%2C471%2074.6%2C100.6%20H%20437.4%20L%20404.4%2C470.8%20255.7%2C512%22%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20style%3D%22fill%3A%23e44d26%22%20%2F%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20id%3D%22path265%22%0A%20%20%20%20%20%20%20%20%20d%3D%22M%20256%2C480.5%20V%20131%20H%20404.3%20L%20376%2C447%22%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20style%3D%22fill%3A%23f16529%22%20%2F%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20id%3D%22path267%22%0A%20%20%20%20%20%20%20%20%20d%3D%22m%20142%2C176.3%20h%20114%20v%2045.4%20h%20-64.2%20l%204.2%2C46.5%20h%2060%20v%2045.3%20H%20154.4%20m%202%2C22.8%20H%20202%20l%203.2%2C36.3%2050.8%2C13.6%20v%2047.4%20l%20-93.2%2C-26%22%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20style%3D%22fill%3A%23ebebeb%22%20%2F%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20id%3D%22path269%22%0A%20%20%20%20%20%20%20%20%20d%3D%22M%20369.6%2C176.3%20H%20255.8%20v%2045.4%20h%20109.6%20m%20-4.1%2C46.5%20H%20255.8%20v%2045.4%20h%2056%20l%20-5.3%2C59%20-50.7%2C13.6%20v%2047.2%20l%2093%2C-25.8%22%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20style%3D%22fill%3A%23ffffff%22%20%2F%3E%0A%20%20%20%20%3C%2Fg%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${hls_image_style}"/>
                    <span style="font-weight: bold;">HLS</span>
                    <span style="display: inline-block; width: 16px;"></span>
                    <img class="${rtmp_image_class}"
                         id="rtmpImage"
                         ${rtmp_image_onclick}
                         src="data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C%21--%20Created%20with%20Inkscape%20%28http%3A%2F%2Fwww.inkscape.org%2F%29%20--%3E%0A%0A%3Csvg%0A%20%20%20xmlns%3Adc%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Felements%2F1.1%2F%22%0A%20%20%20xmlns%3Acc%3D%22http%3A%2F%2Fcreativecommons.org%2Fns%23%22%0A%20%20%20xmlns%3Ardf%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%22%0A%20%20%20xmlns%3Asvg%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%0A%20%20%20xmlns%3Asodipodi%3D%22http%3A%2F%2Fsodipodi.sourceforge.net%2FDTD%2Fsodipodi-0.dtd%22%0A%20%20%20xmlns%3Ainkscape%3D%22http%3A%2F%2Fwww.inkscape.org%2Fnamespaces%2Finkscape%22%0A%20%20%20viewBox%3D%220%200%2016.933333%2016.933334%22%0A%20%20%20version%3D%221.1%22%0A%20%20%20id%3D%22svg51%22%0A%20%20%20inkscape%3Aversion%3D%220.92.3%20%282405546%2C%202018-03-11%29%22%0A%20%20%20sodipodi%3Adocname%3D%22Flash.svg%22%3E%0A%20%20%3Cdefs%0A%20%20%20%20%20id%3D%22defs45%22%3E%0A%20%20%20%20%3ClinearGradient%0A%20%20%20%20%20%20%20id%3D%22linearGradient220%22%0A%20%20%20%20%20%20%20spreadMethod%3D%22pad%22%0A%20%20%20%20%20%20%20gradientTransform%3D%22matrix%28-114.34444%2C120.61603%2C120.61603%2C114.34445%2C356.6875%2C359.46777%29%22%0A%20%20%20%20%20%20%20gradientUnits%3D%22userSpaceOnUse%22%0A%20%20%20%20%20%20%20y2%3D%220%22%0A%20%20%20%20%20%20%20x2%3D%221%22%0A%20%20%20%20%20%20%20y1%3D%220%22%0A%20%20%20%20%20%20%20x1%3D%220%22%3E%0A%20%20%20%20%20%20%3Cstop%0A%20%20%20%20%20%20%20%20%20id%3D%22stop216%22%0A%20%20%20%20%20%20%20%20%20offset%3D%220%22%0A%20%20%20%20%20%20%20%20%20style%3D%22stop-opacity%3A1%3Bstop-color%3A%23b41f24%22%20%2F%3E%0A%20%20%20%20%20%20%3Cstop%0A%20%20%20%20%20%20%20%20%20id%3D%22stop218%22%0A%20%20%20%20%20%20%20%20%20offset%3D%221%22%0A%20%20%20%20%20%20%20%20%20style%3D%22stop-opacity%3A1%3Bstop-color%3A%23d42027%22%20%2F%3E%0A%20%20%20%20%3C%2FlinearGradient%3E%0A%20%20%20%20%3CclipPath%0A%20%20%20%20%20%20%20id%3D%22clipPath230%22%0A%20%20%20%20%20%20%20clipPathUnits%3D%22userSpaceOnUse%22%3E%0A%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20id%3D%22path228%22%0A%20%20%20%20%20%20%20%20%20d%3D%22M%200%2C841.89%20H%20595.28%20V%200%20H%200%20Z%22%20%2F%3E%0A%20%20%20%20%3C%2FclipPath%3E%0A%20%20%3C%2Fdefs%3E%0A%20%20%3Csodipodi%3Anamedview%0A%20%20%20%20%20id%3D%22base%22%0A%20%20%20%20%20pagecolor%3D%22%23ffffff%22%0A%20%20%20%20%20bordercolor%3D%22%23666666%22%0A%20%20%20%20%20borderopacity%3D%221.0%22%0A%20%20%20%20%20inkscape%3Apageopacity%3D%220.0%22%0A%20%20%20%20%20inkscape%3Apageshadow%3D%222%22%0A%20%20%20%20%20inkscape%3Azoom%3D%221%22%0A%20%20%20%20%20inkscape%3Acx%3D%22317%22%0A%20%20%20%20%20inkscape%3Acy%3D%22-40%22%0A%20%20%20%20%20inkscape%3Adocument-units%3D%22mm%22%0A%20%20%20%20%20inkscape%3Acurrent-layer%3D%22layer1%22%0A%20%20%20%20%20showgrid%3D%22false%22%0A%20%20%20%20%20units%3D%22px%22%0A%20%20%20%20%20inkscape%3Awindow-width%3D%221366%22%0A%20%20%20%20%20inkscape%3Awindow-height%3D%22716%22%0A%20%20%20%20%20inkscape%3Awindow-x%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-y%3D%22-8%22%0A%20%20%20%20%20inkscape%3Awindow-maximized%3D%221%22%20%2F%3E%0A%20%20%3Cmetadata%0A%20%20%20%20%20id%3D%22metadata48%22%3E%0A%20%20%20%20%3Crdf%3ARDF%3E%0A%20%20%20%20%20%20%3Ccc%3AWork%0A%20%20%20%20%20%20%20%20%20rdf%3Aabout%3D%22%22%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Aformat%3Eimage%2Fsvg%2Bxml%3C%2Fdc%3Aformat%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atype%0A%20%20%20%20%20%20%20%20%20%20%20rdf%3Aresource%3D%22http%3A%2F%2Fpurl.org%2Fdc%2Fdcmitype%2FStillImage%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%3Cdc%3Atitle%3E%3C%2Fdc%3Atitle%3E%0A%20%20%20%20%20%20%3C%2Fcc%3AWork%3E%0A%20%20%20%20%3C%2Frdf%3ARDF%3E%0A%20%20%3C%2Fmetadata%3E%0A%20%20%3Cg%0A%20%20%20%20%20inkscape%3Alabel%3D%22Layer%201%22%0A%20%20%20%20%20inkscape%3Agroupmode%3D%22layer%22%0A%20%20%20%20%20id%3D%22layer1%22%0A%20%20%20%20%20transform%3D%22translate%280%2C-280.06665%29%22%3E%0A%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20transform%3D%22matrix%280.13229167%2C0%2C0%2C-0.13229167%2C-30.954267%2C344.2797%29%22%0A%20%20%20%20%20%20%20inkscape%3Alabel%3D%22flash_player%22%0A%20%20%20%20%20%20%20id%3D%22g202%22%3E%0A%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20id%3D%22g204%22%3E%0A%20%20%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20%20%20id%3D%22g206%22%3E%0A%20%20%20%20%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20%20%20%20%20id%3D%22g212%22%3E%0A%20%20%20%20%20%20%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20id%3D%22g214%22%3E%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20id%3D%22path222%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20style%3D%22fill%3Aurl%28%23linearGradient220%29%3Bstroke%3Anone%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20d%3D%22m%20361.985%2C358.89%20h%20-128%20v%20125%20h%20128%20z%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20id%3D%22g224%22%3E%0A%20%20%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20%20%20clip-path%3D%22url%28%23clipPath230%29%22%0A%20%20%20%20%20%20%20%20%20%20%20id%3D%22g226%22%3E%0A%20%20%20%20%20%20%20%20%20%20%3Cg%0A%20%20%20%20%20%20%20%20%20%20%20%20%20transform%3D%22translate%28323.4014%2C444.7388%29%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20id%3D%22g232%22%3E%0A%20%20%20%20%20%20%20%20%20%20%20%20%3Cpath%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20inkscape%3Aconnector-curvature%3D%220%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20id%3D%22path234%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20style%3D%22fill%3A%23ffffff%3Bfill-opacity%3A1%3Bfill-rule%3Aevenodd%3Bstroke%3Anone%22%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20d%3D%22m%200%2C0%20c%202.063%2C0.715%204.367%2C1.112%207.067%2C1.112%20v%2016.122%20c%20-11.594%2C0%20-20.886%2C-4.368%20-27.955%2C-13.184%20-2.462%2C-3.097%20-4.924%2C-6.988%20-6.989%2C-11.754%20l%20-5.241%2C-12.786%20c%20-1.827%2C-5.163%20-3.416%2C-8.975%20-4.686%2C-11.515%20-1.668%2C-3.655%20-3.256%2C-6.513%20-4.844%2C-8.578%20-1.986%2C-2.462%20-4.051%2C-4.129%20-6.354%2C-5.243%20-2.542%2C-1.19%20-5.481%2C-1.826%20-8.895%2C-1.826%20v%20-16.28%20c%2011.595%2C0%2020.887%2C4.447%2027.955%2C13.183%201.986%2C2.622%203.892%2C5.639%205.719%2C9.213%20l%204.448%2C10.165%20h%2018.662%20v%2016.202%20h%20-12.31%20c%201.193%2C2.7%202.384%2C5.003%203.654%2C6.989%201.349%2C2.065%202.78%2C3.812%204.289%2C5.004%20C%20-3.813%2C-1.748%20-2.066%2C-0.715%200%2C0%22%20%2F%3E%0A%20%20%20%20%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%20%20%3C%2Fg%3E%0A%20%20%20%20%3C%2Fg%3E%0A%20%20%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A"
                         style="${rtmp_image_style}"/>
                    <span style="font-weight: bold;">RTMP</span>
                </div>
                <footer class="w3-container w3-white">
                    <ul class="w3-ul">
                        <li class="w3-right-align">
                            <button class="w3-button w3-disabled w3-black"
                                    id="settingsResetButton"
                                    onclick="SettingsModule.resetSettings()">Reset
                            </button>
                            <button class="w3-button w3-disabled w3-red"
                                    id="settingsApplyButton"
                                    onclick="SettingsModule.applySettings()">Apply
                            </button>
                        </li>
                    </ul>
                </footer>
            </div>
        </div>
<div id="loadingDiv" class="w3-modal">
            <div class="w3-modal-content">
                <div class="w3-container w3-center">
                    <h2 id="loadingHeader"></h2>
                    <br/>
                    <br/>
                    <span class="fa fa-4x fa-refresh fa-spin"></span>
                </div>
            </div>
        </div>
<div class="w3-container"
     id="contentDiv"
     style="display: none;">
    <div class="w3-border w3-container w3-left"
         id="guideDiv"
         style="overflow-y: auto; width: 100%;">
        <div class="w3-container">
            <ul class="w3-ul"
                id="guideUl"
                style="display: none;">
${guide_lis}
                <li class="w3-border-0 w3-center"
                    id="noMatchingProgramLi"
                    style="display: none;">
                    <p>No programs matching the search pattern found</p>
                </li>
            </ul>
        </div>
    </div>
    <div class="w3-container w3-right"
         id="videoDiv"
         style="display: none; margin: auto;">
    </div>
    <div class="w3-border w3-container"
         id="recordingsDiv"
         style="display: none; overflow-y: auto;">
        <ul class="w3-ul w3-border-0">
            <li>
                <h3>
                    <span style="font-weight: bold">Live Recordings</span>
                    <span class="fa fa-refresh w3-right"
                          id="liveRecordingsRefreshIcon"
                          onclick="RecordingsModule.refreshRecordings('live')"
                          style="cursor: pointer; font-size: 24px;">
                        </span>
                </h3>
            </li>
            <li class="w3-border-0 w3-center"
                id="liveNoRecordingsLi"
                style="${live_no_recordings_li_style}">
                <p>You have no live recordings at the current time
                </p>
            </li>
            <li class="w3-border-0"
                id="liveRecordingsLi"
                style="${live_recordings_li_style}">
                <table class="w3-bordered w3-table"
                       id="liveRecordingsTable">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Channel #</th>
                            <th>Channel Name</th>
                            <th>Program Title</th>
                            <th>Start Date &amp; Time</th>
                            <th>End Date &amp; Time</th>
                        </tr>
                    </thead>
                    <tbody>
${live_recordings_table_rows}
                    </tbody>
                </table>
            </li>
            <li class="w3-border-0">
            </li>
            <li>
                <h3>
                    <span style="font-weight: bold">Saved Recordings</span>
                    <span class="fa fa-refresh w3-right"
                          id="persistedRecordingsRefreshIcon"
                          onclick="RecordingsModule.refreshRecordings('persisted')"
                          style="cursor: pointer; font-size: 24px;">
                        </span>
                </h3>
            </li>
            <li class="w3-border-0 w3-center"
                id="persistedNoRecordingsLi"
                style="${persisted_no_recordings_li_style}">
                <p>You have no saved recordings at the current time
                </p>
            </li>
            <li class="w3-border-0"
                id="persistedRecordingsLi"
                style="${persisted_recordings_li_style}">
                <table class="w3-bordered w3-table"
                       id="persistedRecordingsTable">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Channel #</th>
                            <th>Channel Name</th>
                            <th>Program Title</th>
                            <th>Start Date &amp; Time</th>
                            <th>End Date &amp; Time</th>
                        </tr>
                    </thead>
                    <tbody>
${persisted_recordings_table_rows}
                    </tbody>
                </table>
            </li>
            <li class="w3-border-0">
            </li>
            <li>
                <h3>
                    <span style="font-weight: bold">Scheduled Recordings</span>
                    <span class="fa fa-refresh w3-right"
                          id="scheduledRecordingsRefreshIcon"
                          onclick="RecordingsModule.refreshRecordings('scheduled')"
                          style="cursor: pointer; font-size: 24px;">
                        </span>
                </h3>
            </li>
            <li class="w3-border-0 w3-center"
                id="scheduledNoRecordingsLi"
                style="${scheduled_no_recordings_li_style}">
                <p>You have no scheduled recordings at the current time
                </p>
            </li>
            <li class="w3-border-0"
                id="scheduledRecordingsLi"
                style="${scheduled_recordings_li_style}">
                <table class="w3-bordered w3-table"
                       id="scheduledRecordingsTable">
                    <thead>
                        <tr>
                            <th></th>
                            <th>Channel #</th>
                            <th>Channel Name</th>
                            <th>Program Title</th>
                            <th>Start Date &amp; Time</th>
                            <th>End Date &amp; Time</th>
                        </tr>
                    </thead>
                    <tbody>
${scheduled_recordings_table_rows}
                    </tbody>
                </table>
            </li>
            <li class="w3-border-0">
            </li>
            <li class="w3-border-0">
                <div class="w3-border-no w3-display-container w3-panel"
                     id="recordingsAlertDiv"
                     style="display: none;">
                        <span id="recordingsSpan"
                              onclick="CommonModule.resetAlertDiv('recordingsAlertDiv')"
                              class="w3-button w3-large w3-display-topright">&times;</span>
                    <h3 id="recordingsHeader"></h3>
                    <p class="w3-medium"
                       id="recordingsMessageParagraph"></p>
                    <p class="w3-medium"
                       id="recordingsReasonParagraph"></p>
                </div>
            </li>
            <li class="w3-right-align">
                <button class="w3-button w3-disabled w3-black"
                        id="recordingsClearButton"
                        onclick="RecordingsModule.clearRecordingsRadioButtonGroup()">
                    Clear
                </button>
                <button class="w3-button w3-disabled w3-red"
                        id="recordingsActionButton"
                        onclick="RecordingsModule.deleteRecording()">-
                </button>
            </li>
        </ul>
    </div>
    <div class="w3-border w3-container"
         id="configurationDiv"
         style="display: none; overflow-y: auto;">
        <ul class="w3-ul w3-border-0">
            <li class="w3-border-0">
                <form action=""
                      autocomplete="off"
                      class="w3-container w3-row-padding"
                      id="configurationForm"
                      novalidate="novalidate">
                    <div id="serverConfigurationDiv">
                        <h3>
                            <span style="font-weight: bold;">Server</span>
                        </h3>
                        <p>
                            <label for="serverPasswordInput">Password</label>
                            <span class="fa fa-eye w3-right"
                                  id="serverTogglePasswordSpan"
                                  onclick="ConfigurationModule.togglePasswordVisibility(event)"
                                  style="cursor: pointer;"></span>
                            <input class="w3-border w3-input"
                                   id="serverPasswordInput"
                                   name="serverPasswordInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="password"
                                   value="${configuration_server_password}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverPasswordInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="serverHttpPortInput">HTTP Port Number</label>
                            <input class="w3-border w3-input"
                                   id="serverHttpPortInput"
                                   name="serverHttpPortInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="number"
                                   value="${configuration_server_http_port}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverHttpPortInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="serverHttpsPortInput">HTTPS Port Number</label>
                            <input class="w3-border w3-input"
                                   id="serverHttpsPortInput"
                                   name="serverHttpsPortInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="number"
                                   value="${configuration_server_https_port}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverHttpsPortInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="serverHostnameLoopbackInput">Loopback Hostname</label>
                            <input class="w3-border w3-input"
                                   id="serverHostnameLoopbackInput"
                                   name="serverHostnameLoopbackInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_server_hostname_loopback}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverHostnameLoopbackInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="serverHostnamePrivateInput">Private LAN Hostname</label>
                            <input class="w3-border w3-input"
                                   id="serverHostnamePrivateInput"
                                   name="serverHostnamePrivateInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_server_hostname_private}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverHostnamePrivateInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="serverHostnamePublicInput">Public WAN Hostname</label>
                            <input class="w3-border w3-input"
                                   id="serverHostnamePublicInput"
                                   name="serverHostnamePublicInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_server_hostname_public}" />
                            <span class="w3-font-red w3-tiny"
                                  id="serverHostnamePublicInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                    </div>
                    <div id="smoothstreamsConfigurationDiv">
                        <h3>
                            <span style="font-weight: bold;">SmoothStreams</span>
                        </h3>
                        <p>
                            <label for="smoothStreamsServiceSelect">Service</label>
                            <select class="w3-border w3-select"
                                    id="smoothStreamsServiceSelect"
                                    name="smoothStreamsServiceSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_view247_selected}value="view247">Live247</option>
                                <option ${configuration_viewmmasr_selected}value="viewmmasr">MMA TV</option>
                                <option ${configuration_viewss_selected}value="viewss">StarStreams</option>
                                <option ${configuration_viewstvn_selected}value="viewstvn">StreamTVNow</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsServiceSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsServerSelect">Server</label>
                            <select class="w3-border w3-select"
                                    id="smoothStreamsServerSelect"
                                    name="smoothStreamsServerSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_dap_selected}value="dap">Asia Pacific Mix</option>
                                <option ${configuration_deu_selected}value="deu">Europe Mix</option>
                                <option ${configuration_dna_selected}value="dna">North America Mix</option>
                                <option ${configuration_deu_de_selected}value="deu-de">Europe Germany Mix</option>
                                <option ${configuration_deu_nl_selected}value="deu-nl">Europe Netherlands Mix</option>
                                <option ${configuration_deu_uk_selected}value="deu-uk">Europe UK Mix</option>
                                <option ${configuration_dnae_selected}value="dnae">North America East Mix</option>
                                <option ${configuration_dnaw_selected}value="dnaw">North America West Mix</option>
                                <option ${configuration_deu_nl1_selected}value="deu-nl1">Europe Netherlands 1 (i3d)</option>
                                <option ${configuration_deu_nl2_selected}value="deu-nl2">Europe Netherlands 2 (i3d)</option>
                                <option ${configuration_deu_nl3_selected}value="deu-nl3">Europe Netherlands 3 (Amsterdam)</option>
                                <option ${configuration_deu_nl4_selected}value="deu-nl4">Europe Netherlands 4 (Breda)</option>
                                <option ${configuration_deu_nl5_selected}value="deu-nl5">Europe Netherlands 5 (Enschede)</option>
                                <option ${configuration_deu_uk1_selected}value="deu-uk1">Europe UK 1 (io)</option>
                                <option ${configuration_deu_uk2_selected}value="deu-uk2">Europe UK 2 (100TB)</option>
                                <option ${configuration_dnae1_selected}value="dnae1">North America East 1 (New Jersey)</option>
                                <option ${configuration_dnae2_selected}value="dnae2">North America East 2 (Virginia)</option>
                                <option ${configuration_dnae3_selected}value="dnae3">North America East 3 (Montreal)</option>
                                <option ${configuration_dnae4_selected}value="dnae4">North America East 4 (Toronto)</option>
                                <option ${configuration_dnae6_selected}value="dnae6">North America East 6 (New York)</option>
                                <option ${configuration_dnaw1_selected}value="dnaw1">North America West 1 (Phoenix)</option>
                                <option ${configuration_dnaw2_selected}value="dnaw2">North America West 2 (Los Angeles)</option>
                                <option ${configuration_dnaw3_selected}value="dnaw3">North America West 3 (San Jose)</option>
                                <option ${configuration_dnaw4_selected}value="dnaw4">North America West 4 (Chicago)</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsServerSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsUsernameInput">Username</label>
                            <input class="w3-border w3-input"
                                   id="smoothStreamsUsernameInput"
                                   name="smoothStreamsUsernameInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_smooth_streams_username}" />
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsUsernameInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsPasswordInput">Password</label>
                            <span class="fa fa-eye w3-right"
                                  id="smoothStreamsTogglePasswordSpan"
                                  onclick="ConfigurationModule.togglePasswordVisibility(event)"
                                  style="cursor: pointer;"></span>
                            <input class="w3-border w3-input"
                                   id="smoothStreamsPasswordInput"
                                   name="smoothStreamsPasswordInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="password"
                                   value="${configuration_smooth_streams_password}" />
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsPasswordInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsPlaylistProtocolSelect">Playlist Protocol</label>
                            <select class="w3-border w3-select"
                                    id="smoothStreamsPlaylistProtocolSelect"
                                    name="smoothStreamsPlaylistProtocolSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_smooth_streams_playlist_protocol_hls_selected}value="hls">HTTP Live Streaming (HLS)</option>
                                <option ${configuration_smooth_streams_playlist_protocol_rtmp_selected}value="rtmp">Real-Time Messaging Protocol (RTMP)</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsPlaylistProtocolSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsPlaylistTypeSelect">Playlist Type</label>
                            <select class="w3-border w3-select"
                                    id="smoothStreamsPlaylistTypeSelect"
                                    name="smoothStreamsPlaylistTypeSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_smooth_streams_playlist_type_dynamic_selected}value="dynamic">Dynamic</option>
                                <option ${configuration_smooth_streams_playlist_type_static_selected}value="static">Static</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsPlaylistTypeSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsEpgSourceSelect">EPG Source</label>
                            <select class="w3-border w3-select"
                                    id="smoothStreamsEpgSourceSelect"
                                    name="smoothStreamsEpgSourceSelect"
                                    oninput="ConfigurationModule.determineEpgUrlLabelInputVisibility();ConfigurationModule.determineResetAndUpdateButtonsState();"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_smooth_streams_epg_source_smoothstreams_selected}value="smoothstreams">SmoothStreams (Main)</option>
                                <option ${configuration_smooth_streams_epg_source_fog_selected}value="fog">Fog (Alternative)</option>
                                <option ${configuration_smooth_streams_epg_source_other_selected}value="other">Other (External)</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsEpgSourceSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="smoothStreamsEpgUrlInput"
                                   id="smoothStreamsEpgUrlLabel">EPG Url</label>
                            <input class="w3-border w3-input"
                                   id="smoothStreamsEpgUrlInput"
                                   name="smoothStreamsEpgUrlInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_smooth_streams_epg_url}" />
                            <span class="w3-font-red w3-tiny"
                                  id="smoothStreamsEpgUrlInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                    </div>
                    <div id="vaderstreamsConfigurationDiv">
                        <h3>
                            <span style="font-weight: bold;">VaderStreams</span>
                        </h3>
                        <p>
                            <label for="vaderStreamsServerSelect">Server</label>
                            <select class="w3-border w3-select"
                                    id="vaderStreamsServerSelect"
                                    name="vaderStreamsServerSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option selected="selected"
                                        value="auto">Auto</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="vaderStreamsServerSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="vaderStreamsUsernameInput">Username</label>
                            <input class="w3-border w3-input"
                                   id="vaderStreamsUsernameInput"
                                   name="vaderStreamsUsernameInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="text"
                                   value="${configuration_vader_streams_username}" />
                            <span class="w3-font-red w3-tiny"
                                  id="vaderStreamsUsernameInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="vaderStreamsPasswordInput">Password</label>
                            <span class="fa fa-eye w3-right"
                                  id="vaderStreamsTogglePasswordSpan"
                                  onclick="ConfigurationModule.togglePasswordVisibility(event)"
                                  style="cursor: pointer;"></span>
                            <input class="w3-border w3-input"
                                   id="vaderStreamsPasswordInput"
                                   name="vaderStreamsPasswordInput"
                                   oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                   type="password"
                                   value="${configuration_vader_streams_password}" />
                            <span class="w3-font-red w3-tiny"
                                  id="vaderStreamsPasswordInputErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="vaderStreamsPlaylistProtocolSelect">Playlist Protocol</label>
                            <select class="w3-border w3-select"
                                    id="vaderStreamsPlaylistProtocolSelect"
                                    name="vaderStreamsPlaylistProtocolSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_vader_streams_playlist_protocol_hls_selected}value="hls">HTTP Live Streaming (HLS)</option>
                                <option ${configuration_vader_streams_playlist_protocol_mpegts_selected}value="mpegts">MPEG Transport Stream (MPEG-TS)</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="vaderStreamsPlaylistProtocolSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                        <p>
                            <label for="vaderStreamsPlaylistTypeSelect">Playlist Type</label>
                            <select class="w3-border w3-select"
                                    id="vaderStreamsPlaylistTypeSelect"
                                    name="vaderStreamsPlaylistTypeSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_vader_streams_playlist_type_dynamic_selected}value="dynamic">Dynamic</option>
                                <option ${configuration_vader_streams_playlist_type_static_selected}value="static">Static</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="vaderStreamsPlaylistTypeSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                    </div>
                    <div id="loggingConfigurationDiv">
                        <h3>
                            <span style="font-weight: bold;">Logging</span>
                        </h3>
                        <p>
                            <label for="loggingLevelSelect">Level</label>
                            <select class="w3-border w3-select"
                                    id="loggingLevelSelect"
                                    name="loggingLevelSelect"
                                    oninput="ConfigurationModule.determineResetAndUpdateButtonsState()"
                                    style="padding: 8px;">
                                <option disabled="disabled"
                                        selected="selected"
                                        value="">Choose your option
                                </option>
                                <option ${configuration_info_selected}value="INFO">Info</option>
                                <option ${configuration_debug_selected}value="DEBUG">Debug</option>
                                <option ${configuration_trace_selected}value="TRACE">Trace</option>
                            </select>
                            <span class="w3-font-red w3-tiny"
                                  id="loggingLevelSelectErrorSpan"
                                  style="color: red;"></span>
                        </p>
                    </div>
                </form>
            </li>
            <li class="w3-border-0">
                <div class="w3-border-no w3-display-container w3-panel"
                     id="configurationAlertDiv"
                     style="display: none;">
                        <span id="configurationSpan"
                              onclick="CommonModule.resetAlertDiv('configurationAlertDiv')"
                              class="w3-button w3-large w3-display-topright">&times;</span>
                    <h3 id="configurationHeader"></h3>
                    <p class="w3-medium"
                       id="configurationMessageParagraph"></p>
                    <p class="w3-medium"
                       id="configurationReasonParagraph"></p>
                </div>
            </li>
            <li class="w3-border-0">
                <div class="w3-right-align">
                    <button class="w3-button w3-black w3-disabled"
                            id="configurationResetButton"
                            onclick="ConfigurationModule.resetConfiguration()">
                        Reset
                    </button>
                    <button class="w3-button w3-red w3-disabled"
                            id="updateConfigurationButton"
                            onclick="ConfigurationModule.updateConfiguration()">Update
                    </button>
                </div>
            </li>
    </div>
    <div class="w3-border w3-container"
         id="monitorDiv"
         style="display: none; overflow-y: auto;">
        <h2>Coming soon...</h2>
    </div>
    <div class="w3-border w3-container"
         id="aboutDiv"
         style="display: none; overflow-y: auto">
        <h2>SmoothStreams Proxy ${iptv_proxy_version}</h2>
    </div>
</div>
</body>
</html>