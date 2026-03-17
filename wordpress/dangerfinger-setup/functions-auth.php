<?php
/**
 * DangerFinger WordPress JWT auth integration + shortcode.
 *
 * Add this code to your active theme's functions.php (or a custom mu-plugin).
 * This file is maintained in the danger-finger repo for reference:
 *   wordpress/dangerfinger-setup/functions-auth.php
 *
 * Prerequisites:
 *   - "JWT Authentication for WP REST API" plugin installed and active
 *   - JWT_AUTH_SECRET_KEY and JWT_AUTH_CORS_ENABLE defined in wp-config.php
 *     (see wp-config-additions.txt)
 *   - Authorization header passthrough added to .htaccess
 *     (see htaccess-additions.txt)
 */

// ---------------------------------------------------------------------------
// 1. Add user_nicename to JWT payload so Tornado can identify the user
//    without a separate WP API call.
// ---------------------------------------------------------------------------
add_filter('jwt_auth_token_before_sign', function ($token, $user) {
    $token['data']['user']['user_nicename'] = $user->user_nicename;
    $token['data']['user']['user_display_name'] = $user->display_name;
    return $token;
}, 10, 2);

// ---------------------------------------------------------------------------
// 2. Add CORS headers for the JWT token endpoint so the app can call it
//    cross-origin from the AWS domain.
//    (JWT_AUTH_CORS_ENABLE=true in wp-config.php handles this for the plugin,
//    but this filter ensures our app origin is explicitly allowed.)
// ---------------------------------------------------------------------------
add_filter('jwt_auth_cors_allow_headers', function ($headers) {
    $headers[] = 'Authorization';
    return $headers;
});

// ---------------------------------------------------------------------------
// 3. Shortcode: [dangerfinger_configurator]
//
//    Usage on WordPress page/post:
//      [dangerfinger_configurator url="https://your-aws-app.example.com/"]
//
//    Shows iframe for logged-in users; login prompt for guests.
//    After login, WordPress redirects back with Application Password so the
//    app can exchange it for a JWT.
// ---------------------------------------------------------------------------
add_shortcode('dangerfinger_configurator', function ($atts) {
    $atts = shortcode_atts([
        'url'    => defined('DANGERFINGER_APP_URL') ? DANGERFINGER_APP_URL : '',
        'height' => '900',
    ], $atts, 'dangerfinger_configurator');

    $app_url = esc_url(trailingslashit($atts['url']));
    $height  = intval($atts['height']);

    if (!$app_url) {
        return '<p class="df-error">DangerFinger app URL not configured. '
             . 'Set <code>define(\'DANGERFINGER_APP_URL\', \'https://...\');</code> in wp-config.php '
             . 'or pass <code>url=""</code> to the shortcode.</p>';
    }

    // Build the authorize-application redirect so the user logs in and
    // then grants the app an Application Password in one step.
    $success_url = add_query_arg('jwt_auth', '1', $app_url);
    $auth_url = admin_url('authorize-application.php') . '?'
        . http_build_query([
            'app_name'    => 'DangerFinger',
            'app_id'      => 'dangerfinger-configurator',
            'success_url' => $success_url,
            'reject_url'  => $app_url,
        ]);

    $guest_notice = '';
    if (!is_user_logged_in()) {
        $guest_notice = '<div class="df-login-prompt" style="text-align:center;padding:1em 1em 0;">'
            . '<p style="margin-bottom:0.75em;">Preview and configure anonymously. Log in only when you want to save a model to your profile.</p>'
            . '<a class="button" href="' . esc_url($auth_url) . '">Log in and authorise</a>'
            . '</div>';
    }

    $iframe_url = $app_url;
    return $guest_notice
         . '<div class="df-iframe-wrapper" style="width:100%;overflow:hidden;">'
         . '<iframe src="' . esc_url($iframe_url) . '" '
         . 'width="100%" height="' . $height . '" '
         . 'style="border:none;display:block;" '
         . 'allow="fullscreen" loading="lazy">'
         . '</iframe>'
         . '</div>';
});

// ---------------------------------------------------------------------------
// 4. Fullscreen wrapper: ?fullscreen=1 on the configure page renders a
//    full-viewport iframe with a thin breadcrumb/back bar, keeping the user
//    on the dangercreations.com domain.
// ---------------------------------------------------------------------------
add_action('template_redirect', function () {
    if (!isset($_GET['fullscreen']) || !defined('DANGERFINGER_APP_URL')) return;
    if (!is_page('configure')) return;

    $app_url = esc_url(trailingslashit(DANGERFINGER_APP_URL));
    $wp_url  = home_url('/prosthetics/');
    $cfg_url = home_url('/prosthetics/configure/');

    header('Content-Type: text/html; charset=utf-8');
    ?><!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DangerFinger Configurator &ndash; Danger Creations</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{display:flex;flex-direction:column;height:100vh;overflow:hidden;background:#343a40}
    #df-topbar{display:flex;align-items:center;gap:10px;padding:6px 14px;background:#343a40;color:#adb5bd;font:13px/1.4 system-ui,sans-serif;flex-shrink:0}
    #df-topbar a{color:#adb5bd;text-decoration:none}
    #df-topbar a:hover{color:#fff}
    #df-topbar .sep{opacity:.4}
    iframe{flex:1;border:none;display:block;width:100%}
  </style>
</head>
<body>
  <div id="df-topbar">
    <a href="<?= esc_url($wp_url) ?>">&#8592; Danger Creations</a>
    <span class="sep">|</span>
    <a href="<?= esc_url($cfg_url) ?>">Prosthetics</a>
    <span class="sep">&rsaquo;</span>
    <span>Configure</span>
  </div>
  <iframe id="df-frame" src="<?= esc_url($app_url) ?>" allow="fullscreen" allowfullscreen></iframe>
  <script>
    (function(){
      var h = window.location.hash;
      if (h) document.getElementById('df-frame').src = <?= json_encode($app_url) ?> + h;
    })();
  </script>
</body>
</html><?php
    exit;
});
