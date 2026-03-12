<?php
/**
 * DangerFinger WordPress security hardening.
 *
 * Add this code to your active theme's functions.php (or a custom mu-plugin).
 * This file is maintained in the danger-finger repo for reference:
 *   wordpress/dangerfinger-setup/functions-security.php
 */

// ---------------------------------------------------------------------------
// 1. Disable user enumeration via REST API /?author=N redirect
// ---------------------------------------------------------------------------
add_action('template_redirect', function () {
    if (!is_admin() && isset($_SERVER['REQUEST_URI'])) {
        $request = $_SERVER['REQUEST_URI'];
        if (preg_match('/\?author=([0-9]*)/', $request, $matches)) {
            wp_redirect(home_url(), 301);
            exit;
        }
    }
});

// Also block the /wp-json/wp/v2/users endpoint for non-admins
add_filter('rest_endpoints', function ($endpoints) {
    if (!current_user_can('list_users')) {
        if (isset($endpoints['/wp/v2/users'])) {
            unset($endpoints['/wp/v2/users']);
        }
        if (isset($endpoints['/wp/v2/users/(?P<id>[\d]+)'])) {
            unset($endpoints['/wp/v2/users/(?P<id>[\d]+)']);
        }
    }
    return $endpoints;
});

// ---------------------------------------------------------------------------
// 2. Disable open user registration (belt-and-suspenders; also set in WP admin)
// ---------------------------------------------------------------------------
add_action('init', function () {
    if (get_option('users_can_register')) {
        update_option('users_can_register', 0);
    }
});

// ---------------------------------------------------------------------------
// 3. Strip EXIF / GPS metadata from REST API media responses
// ---------------------------------------------------------------------------
add_filter('rest_prepare_attachment', function ($response, $post, $request) {
    $data = $response->get_data();
    // Remove metadata that may contain GPS/EXIF fields
    if (isset($data['media_details']['image_meta'])) {
        $allowed_meta = ['width', 'height', 'file', 'sizes'];
        foreach (array_keys($data['media_details']) as $key) {
            if (!in_array($key, $allowed_meta, true)) {
                unset($data['media_details'][$key]);
            }
        }
    }
    $response->set_data($data);
    return $response;
}, 10, 3);

// ---------------------------------------------------------------------------
// 4. Remove WordPress version from public pages (minor hardening)
// ---------------------------------------------------------------------------
remove_action('wp_head', 'wp_generator');
add_filter('the_generator', '__return_empty_string');
