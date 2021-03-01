import os
import logging
import flask
import json
import sonormal.utils
import sonormal.normalize
import sonormal.getjsonld

from . import jldextract


def create_app(test_config=None):
    app = flask.Flask(__name__, instance_relative_config=True, static_url_path="")
    if test_config == None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    options = {}
    app.register_blueprint(jldextract.jldex, url_prefix="/jldex", **options)

    @app.template_filter()
    def datetimeToJsonStr(dt):
        return sonormal.utils.datetimeToJsonStr(dt)

    @app.template_filter()
    def asjson(jobj):
        if jobj is not None:
            return json.dumps(jobj, indent=2)
        return ""

    @app.route("/")
    def index_page():
        return flask.render_template("index.html")

    @app.route("/e/")
    def extract_jsonld():
        source_url = flask.request.args.get("url", None)
        if source_url is None:
            return flask.redirect("/")
        if not source_url.startswith("http"):
            flask.abort(404)
        logging.debug("URL = %s", source_url)
        jsonld, responses = sonormal.getjsonld.downloadJson(source_url)
        response = app.response_class(
            response=json.dumps(jsonld, indent=2),
            mimetype="application/ld+json",
        )
        return response

    @app.route("/n/")
    def normalize_so():
        source_url = flask.request.args.get("url", None)
        if source_url is None:
            return flask.redirect("/")
        if not source_url.startswith("http"):
            flask.abort(404)
        logging.debug("URL = %s", source_url)
        jsonld, responses = sonormal.getjsonld.downloadJson(source_url)
        opts = {"base": responses.url}
        jsonld_normalized = sonormal.normalize.normalizeJsonld(jsonld, options=opts)
        response = app.response_class(
            response=json.dumps(jsonld_normalized, indent=2),
            mimetype="application/ld+json",
        )
        return response

    @app.route("/f/")
    def frame_so():
        source_url = flask.request.args.get("url", None)
        if source_url is None:
            return flask.redirect("/")
        if not source_url.startswith("http"):
            flask.abort(404)
        do_normalize = flask.request.args.get("n", False)
        logging.debug("URL = %s", source_url)
        jsonld, _ = sonormal.getjsonld.downloadJson(source_url)
        if do_normalize:
            jsonld = sonormal.normalize.normalizeJsonld(jsonld)
        jsonld_framed = sonormal.normalize.frameSODataset(jsonld)
        response = app.response_class(
            response=json.dumps(jsonld_framed, indent=2),
            mimetype="application/ld+json",
        )
        return response

    @app.route("/i/")
    def extract_identifiers():
        source_url = flask.request.args.get("url", None)
        if source_url is None:
            return flask.redirect("/")
        if not source_url.startswith("http"):
            flask.abort(404)
        do_normalize = flask.request.args.get("n", False)
        do_frame = flask.request.args.get("f", False)
        logging.debug("URL = %s", source_url)
        jsonld, _ = sonormal.getjsonld.downloadJson(source_url)
        if do_normalize:
            jsonld = sonormal.normalize.normalizeJsonld(jsonld)
        if do_frame:
            jsonld = sonormal.normalize.frameSODataset(jsonld)
        identifiers = sonormal.normalize.getDatasetsIdentifiers(jsonld)
        response = app.response_class(
            response=json.dumps(identifiers, indent=2),
            mimetype="application/json",
        )
        return response

    @app.route("/c/")
    def canonicalize():
        source_url = flask.request.args.get("url", None)
        if source_url is None:
            return flask.redirect("/")
        if not source_url.startswith("http"):
            flask.abort(404)
        do_normalize = flask.request.args.get("n", False)
        logging.debug("URL = %s", source_url)
        jsonld, responses = sonormal.getjsonld.downloadJson(source_url)
        if do_normalize:
            opts = {"base": responses.url}
            jsonld = sonormal.normalize.normalizeJsonld(jsonld, options=opts)
        cdoc = sonormal.normalize.canonicalizeJson(jsonld)
        response = app.response_class(
            response=cdoc,
            mimetype="application/ld+json",
        )
        return response

    return app