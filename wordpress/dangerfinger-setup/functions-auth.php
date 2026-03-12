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

    if (!is_user_logged_in()) {
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

        return '<div class="df-login-prompt" style="text-align:center;padding:2em;">'
             . '<p>You must be logged in to use the DangerFinger configurator.</p>'
             . '<a class="button" href="' . esc_url($auth_url) . '">Log in and authorise</a>'
             . '</div>';
    }

    // Logged-in: embed the app in an iframe
    $iframe_url = $app_url;
    return '<div class="df-iframe-wrapper" style="width:100%;overflow:hidden;">'
         . '<iframe src="' . esc_url($iframe_url) . '" '
         . 'width="100%" height="' . $height . '" '
         . 'style="border:none;display:block;" '
         . 'allow="fullscreen" loading="lazy">'
         . '</iframe>'
         . '</div>';
});
