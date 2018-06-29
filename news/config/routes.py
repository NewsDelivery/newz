class Route:
    """ A basic Flask router, used for the most basic form of flask routes,
    namely functionally based views which would normally use the ``@route``
    decorator.
    .. versionadded:: 2014.05.19
    Example
    -------
    .. sourcecode:: python
        from flask.ext.via.routes import default
        from yourapp.views import foo_view, bar_view
        routes = [
            default.Functional('/foo', 'foo', foo_view),
            default.Functional('/bar', 'bar', bar_view),
        ]
    """

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
        self.methods = methods or ['GET']

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
        if 'url_prefix' in kwargs:
            url = kwargs['url_prefix'] + url

        #: If this route was included a endpoint prefix may have been passed
        #: to the route
        if 'endpoint' in kwargs:
            if endpoint is None:
                endpoint = self.func.__name__
            endpoint = kwargs['endpoint'] + endpoint

        try:
            app.add_url_rule(url, endpoint, self.func, methods=self.methods)
        except AssertionError:
            app.logger.warning('routes: couldn\'t add "{}", endpoint "{}" to router'.format(url, endpoint))


def register_routes(app):
    from news.views.web import index, index_rss, new, best, trending, how_it_works, get_help, terms, privacy, rules, jobs, metrics
    from news.views.user import users_profile, users_posts, users_comments, saved_links
    from news.views.settings import profile_settings, account_settings, post_new_password, preferences_setting
    from news.views.search import search
    from news.views.feed import new_feed, get_feed, get_feed_rss, add_link, remove_link, subscribe, unsubscribe
    from news.views.auth import signup, post_signup, post_login, login, logout, reset_password, post_reset_password, set_password, verify

    from news.views.links import get_link
    from news.views.links import link_report
    from news.views.links import post_link_report
    from news.views.links import comment_link
    from news.views.links import save_link
    from news.views.comments import comment_report
    from news.views.comments import post_comment_report
    from news.views.comments import remove_comment
    from news.views.comments import do_comment_vote
    from news.views.links import do_vote
    from news.views.settings import settings
    from news.views.feed import add_admin
    from news.views.feed import feed_admins
    from news.views.feed import feed_admin
    from news.views.feed import post_feed_admin
    from news.views.feed import feed_bans
    from news.views.feed import feed_reports
    from news.views.feed import ban_user
    from news.views.feed import post_ban_user
    routes = [
        # WEB
        Route('/', index),
        Route('/rss', index_rss),
        Route('/new', new),
        Route('/best', best),
        Route('/trending', trending),
        Route('/how-it-works', how_it_works),
        Route('/help', get_help),
        Route('/terms', terms),
        Route('/conditions', terms),
        Route('/privacy', privacy),
        Route('/rules', rules),
        Route('/jobs', jobs),

        # AUTH
        Route('/join', signup),
        Route('/join', post_signup, methods=['POST']),
        Route('/login', login),
        Route('/login', post_login, methods=['POST']),
        Route('/logout', logout),
        Route('/logout', logout),
        Route('/reset_password', reset_password),
        Route('/reset_password', post_reset_password, methods=['POST']),
        Route('/reset_password/<token>', set_password, methods=['POST', 'GET']),
        Route('/verify/<token>', verify),

        # FEED
        Route('/new_feed', new_feed),
        Route('/f/<feed:feed>', get_feed),
        Route('/f/<feed:feed>/<any(trending, new, best):sort>', get_feed),
        Route('/f/<feed:feed>/rss', get_feed_rss),
        Route('/f/<feed:feed>/add', add_link, methods=['GET', 'POST']),
        Route('/f/<feed:feed>/<link_slug>/remove', remove_link, methods=['GET', 'POST']),
        Route('/f/<feed:feed>/subscribe', subscribe),
        Route('/f/<feed:feed>/unsubscribe', unsubscribe),

        # FEED ADMIN
        Route('/f/<feed:feed>/admin', feed_admin),
        Route('/f/<feed:feed>/admin', post_feed_admin, methods=['POST']),
        Route('/f/<feed:feed>/add_admin', add_admin, methods=['POST']),
        Route('/f/<feed:feed>/admins', feed_admins),
        Route('/f/<feed:feed>/bans', feed_bans),
        Route('/f/<feed:feed>/ban/<username>', ban_user),
        Route('/f/<feed:feed>/ban/<username>', post_ban_user, methods=['POST']),
        Route('/f/<feed:feed>/reports', feed_reports),

        # LINKS
        Route('/l/<link:link>', get_link),
        Route('/l/<link:link>/report', link_report),
        Route('/l/<link:link>/report', post_link_report, methods=['POST']),
        Route('/l/<link:link>/comment', comment_link),
        Route('/l/<link:link>/save', save_link),
        Route('/l/<link>/vote/<vote_str>', do_vote),

        # COMMENTS
        Route('/c/<comment:comment>/report', comment_report),
        Route('/c/<comment:comment>/report', post_comment_report, methods=['POST']),
        Route('/c/<comment:comment>/remove', remove_comment),
        Route('/c/<comment:comment>/vote/<vote_str>', do_comment_vote),

        # USER
        Route('/u/<username>', users_profile),
        Route('/u/<username>/posts', users_posts),
        Route('/u/<username>/comments', users_comments),

        # OTHER
        Route('/saved', saved_links),

        # METRICS todo remove
        Route('/metrics', metrics),

        # SEARCH
        Route('/search', search),

        # SETTINGS
        Route('/settings', settings),
        Route('/settings/profile', profile_settings),
        Route('/settings/account', account_settings),
        Route('/settings/preferences', preferences_setting),
        Route('/settings/password', post_new_password, methods=['POST']),
    ]

    for route in routes:
        route.add_to_app(app)
