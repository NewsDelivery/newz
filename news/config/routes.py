from news.controllers.admin import *
from news.controllers.auth import *
from news.controllers.comments import *
from news.controllers.feeds import *
from news.controllers.links import *
from news.controllers.search import *
from news.controllers.settings import *
from news.controllers.user import *
from news.controllers.web import *


class Route:
    def __init__(self, url, func, endpoint=None, methods=None):
        """ Basic router constructor, stores passed arguments on the
        instance.
        Arguments
        ---------
        url : str
            The url to use for the route
        func : function
            The view function to connect the route with
        Keyword Arguments
        -----------------
        endpoint : str, optional
            Optional endpoint string, by default flask will use the
            view function name as the endpoint name, use this argument
            to change the endpoint name.
        """

        self.url = url
        self.func = func
        self.endpoint = endpoint
        self.methods = methods or ["GET"]

    def add_to_app(self, app, **kwargs):
        """ Adds the url route to the flask application object.mro
        .. versionchanged:: 2014.05.08
            * ``url_prefix`` can now be prefixed if present in kwargs
        .. versionchanged:: 2014.05.19
            * ``endpoint`` can now be prefixed if present in kwargs
        Arguments
        ---------
        app : flask.app.Flask
            Flask application instance
        \*\*kwargs
            Arbitrary keyword arguments passed in to ``init_app``
        """

        url = self.url
        endpoint = self.endpoint

        #: If this route was included a url prefix may have been passed
        #: to the route
        if "url_prefix" in kwargs:
            url = kwargs["url_prefix"] + url

        #: If this route was included a endpoint prefix may have been passed
        #: to the route
        if "endpoint" in kwargs:
            if endpoint is None:
                endpoint = self.func.__name__
            endpoint = kwargs["endpoint"] + endpoint

        try:
            app.add_url_rule(url, endpoint, self.func, methods=self.methods)
        except AssertionError:
            app.logger.warning(
                'routes: couldn\'t add "{}", endpoint "{}" to router'.format(
                    url, endpoint
                )
            )


def register_routes(app):
    routes = [
        # WEB
        Route("/", index),
        Route("/rss", index_rss),
        Route("/new", new),
        Route("/best", best),
        Route("/trending", trending),
        Route("/how-it-works", how_it_works),
        Route("/help", get_help),
        Route("/contact", contact),
        Route("/terms", terms),
        Route("/conditions", terms),
        Route("/privacy", privacy),
        Route("/rules", rules),
        Route("/jobs", jobs),
        Route("/suggest-feed", suggest_feed),
        # AUTH
        Route("/join", signup),
        Route("/join", post_signup, methods=["POST"]),
        Route("/login", login, "login"),
        Route("/login", post_login, methods=["POST"]),
        Route("/logout", logout),
        Route("/logout", logout),
        Route("/reset_password", reset_password),
        Route("/reset_password", post_reset_password, methods=["POST"]),
        Route("/reset_password/<token>", set_password, methods=["POST", "GET"]),
        Route("/send_verify", resend_verify),
        Route("/verify/<token>", verify),
        # FEED
        Route("/new_feed", new_feed, methods=["GET", "POST"]),
        Route("/f/<feed:feed>", get_feed),
        Route("/f/<feed:feed>/<any(trending, new, best):sort>", get_feed),
        Route("/f/<feed:feed>/rss", get_feed_rss),
        Route("/f/<feed:feed>/add", add_link, methods=["GET", "POST"]),
        Route("/f/<feed:feed>/<link_id>/remove", remove_link, methods=["GET", "POST"]),
        Route("/f/<feed:feed>/subscribe", subscribe),
        Route("/f/<feed:feed>/unsubscribe", unsubscribe),
        # FEED ADMIN
        Route("/f/<feed:feed>/admin", GET_feed_admin),
        Route("/f/<feed:feed>/admin", POST_feed_admin, methods=["POST"]),
        Route("/f/<feed:feed>/add_admin", add_admin, methods=["POST"]),
        Route("/f/<feed:feed>/admins", feed_admins),
        Route("/f/<feed:feed>/bans", GET_feed_bans),
        Route("/f/<feed:feed>/ban/<username>", ban_user),
        Route("/f/<feed:feed>/ban/<username>", post_ban_user, methods=["POST"]),
        Route("/f/<feed:feed>/reports", feed_reports),
        Route("/f/<feed:feed>/fqs", feed_fqs),
        Route("/f/<feed:feed>/fqs/add", post_feed_fqs, methods=["POST"]),
        Route("/f/<feed:feed>/fqs/<fqs_id>/update", update_fqs),
        Route("/f/<feed:feed>/fqs/<fqs_id>/remove", remove_fqs),
        # LINKS
        Route("/l/<link:link>", get_link),
        Route("/l/<link:link>/remove", remove_link),
        Route("/l/<link:link>/report", link_report),
        Route("/l/<link:link>/report", post_link_report, methods=["POST"]),
        Route("/l/<link:link>/comment", comment_link, methods=["POST"]),
        Route("/l/<link:link>/save", save_link),
        Route("/l/<link:link>/vote/<vote_str>", do_vote),
        Route("/l/<link:link>/<link_slug>", get_link),
        # COMMENTS
        Route("/c/<comment:comment>/report", comment_report),
        Route("/c/<comment:comment>/report", post_comment_report, methods=["POST"]),
        Route("/c/<comment:comment>/remove", remove_comment),
        Route("/c/<comment:comment>/vote/<vote_str>", do_comment_vote),
        # USER
        Route("/u/<username>", users_profile),
        Route("/u/<username>/posts", users_posts),
        Route("/u/<username>/comments", users_comments),
        # OTHER
        Route("/saved", saved_links),
        # SEARCH
        Route("/search", search),
        # SETTINGS
        Route("/settings", settings),
        Route("/settings/profile", profile_settings, methods=["GET", "POST"]),
        Route("/settings/account", account_settings),
        Route("/settings/preferences", preferences_setting),
        Route("/settings/preferences", post_preferences_setting, methods=["POST"]),
        Route("/settings/password", post_new_password, methods=["POST"]),
        Route("/settings/deactivate", post_deactivate, methods=["POST"]),
        Route("/settings/email", post_change_email, methods=["POST"]),
        # OTHER todo remove
        Route("/metrics", metrics),
        Route("/admin", admin),
        Route("/add-testing-data", add_testing_data),
        Route("/clear-cache", clear_cache),
        Route("/trigger-fqs-update", trigger_fqs_update),
    ]

    for route in routes:
        route.add_to_app(app)
