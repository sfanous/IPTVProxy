                <li class="w3-bar${channel_li_border}"
                    id="${channel_li_id_prefix}_channelLi">
                    <img alt="${channel_li_channel_name}"
                         class="w3-bar-item w3-hide-small"
                         src="${channel_li_channel_img_src}"
                         style="width: 85px;" />
                    <div class="w3-bar-item">
                        <span class="w3-large"
                              id="${channel_li_id_prefix}_channelDetailsSpan">${channel_li_channel_number} - ${channel_li_channel_name}</span>
                        <br />
                    </div>
                    <div class="w3-bar-item w3-right">
                        <span class="fa fa-play"
                              data-json='${channel_sources_data_json}'
                              onclick="VideoPlayerModule.controlVideo(event)"
                              style="cursor: pointer;"></span>
                        <span style="display: inline-block; width: 10px;"></span>
                        <span id="${channel_li_id_prefix}_channelFoldingSpan"
                              class="fa fa-plus"
                              onclick="GuideModule.toggleChannelProgramsLi('${channel_li_id_prefix}')"
                              style="cursor: pointer;"></span>
                    </div>
                </li>