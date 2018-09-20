<!DOCTYPE html>
<html lang="en">
<head>
    <link href="https://www.w3schools.com/w3css/4/w3.css"
          rel="stylesheet"/>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1"
          name="viewport">
    <script crossorigin="anonymous"
            integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
            src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script>
        $(document).ready(function () {
            LoginModule.init();
        });

        const LoginModule = (function () {
            let _loginButton = null;
            let _passwordInput = null;

            const _disableLoginButton = function () {
               _loginButton.addClass('w3-disabled');
            };

            const _enableLoginButton = function () {
                _loginButton.removeClass('w3-disabled');
            };

            const determineLoginButtonState = function () {
                if (_passwordInput.val().length) {
                    _enableLoginButton()
                } else {
                    _disableLoginButton()
                }
            };

            const init = function () {
                _loginButton = $('#loginButton');
                _passwordInput = $('#passwordInput');
            };

            return {
                determineLoginButtonState: determineLoginButtonState,
                init: init
            }
        })();
    </script>
    <style>
        body {
            display: flex;
        }

        html, body {
            height: 100%;
            margin: 0;
            width: 100%;
        }

        form {
            margin: auto;
        }
    </style>
    <title>IPTV Proxy ${iptv_proxy_version}</title>
</head>
<body>
    <form action="/index.html"
          autocomplete="off"
          id="loginForm"
          method="post"
          novalidate="novalidate">
        <label for="passwordInput"
               style="font-weight: bold; margin-bottom: 8px;">Password:</label>
        <input class="w3-border w3-input"
               id="passwordInput"
               name="passwordInput"
               oninput="LoginModule.determineLoginButtonState()"
               type="password">
        <button class="w3-black w3-button w3-disabled w3-right"
                id="loginButton"
                style="margin-top: 8px;"
                type="submit">Login
        </button>
    </form>
</body>
</html>