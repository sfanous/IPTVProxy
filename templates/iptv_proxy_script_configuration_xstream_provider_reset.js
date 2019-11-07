            _{{ provider_name_camel_case }}UrlInput.val(data['data']['attributes']['{{ provider_name_snake_case }}_url']);
            _{{ provider_name_camel_case }}UsernameInput.val(data['data']['attributes']['{{ provider_name_snake_case }}_username']);
            _{{ provider_name_camel_case }}PasswordInput.val(data['data']['attributes']['{{ provider_name_snake_case }}_password']);
            _{{ provider_name_camel_case }}PlaylistProtocolSelect.val(data['data']['attributes']['{{ provider_name_snake_case }}_playlist_protocol'].toLowerCase());
            _{{ provider_name_camel_case }}PlaylistTypeSelect.val(data['data']['attributes']['{{ provider_name_snake_case }}_playlist_type'].toLowerCase());
            _{{ provider_name_camel_case }}EpgSourceSelect.val(data['data']['attributes']['{{ provider_name_snake_case }}_epg_source'].toLowerCase());
            _{{ provider_name_camel_case }}EpgUrlInput.val(data['data']['attributes']['{{ provider_name_snake_case }}_epg_url']);