from sponge import app
from flask import jsonify, request, abort
import uuid
from datetime import datetime
from orm import db, DbRelease, DbPackage, DbResults


class Release:
    def __init__(self, notes, references, platforms):
        self.start = datetime.now()
        self.notes = notes
        self.references = references
        self.platforms = platforms
        self.id = uuid.uuid4()

    @staticmethod
    def create_from(request):
        return Release(request.json.get('notes'),
                       request.json.get('references', []),
                       request.json['platforms'])


@app.route('/release', methods=['POST'])
def post_release():
    _validate_release_input(request)
    release = Release.create_from(request)

    app.logger.info('Release notes: %s, references: %s, platforms: %s', release.notes, release.references,
                    release.platforms)
    app.logger.info('Posting release for id: %s', release.id)

    dbRelease = DbRelease(str(release.id), release.platforms[0], 'nobody',
                          next(iter(release.references), ''), release.notes)
    dbRelease.start()

    db.session.add(dbRelease)
    db.session.commit()

    return jsonify(id=release.id)


def _validate_release_input(request):
    if not request.json or not 'platforms' in request.json:
        abort(400)


@app.route('/release/<id>/packages', methods=['POST'])
def post_packages(id):
    if _package_input_is_valid(request, id):
        app.logger.info('Releasing package name: %s and version: %s, for release: %s', request.json['name'],
                        request.json['version'], id)
        package_id = uuid.uuid4()
        app.logger.info('Package id: %s', str(package_id))

        dbPackage = DbPackage(
            str(package_id),
            request.json['name'],
            request.json['version'],
            id)
        dbPackage.start()
        db.session.add(dbPackage)
        db.session.commit()

        return jsonify(id=package_id)
    else:
        # TODO have a proper error handler!
        abort(400)


def _package_input_is_valid(request, id):
    if not request.json:
        app.logger.error("Missing JSON body.")
        return False

    if not 'name' in request.json or not 'version' in request.json:
        app.logger.error("Missing name / version in request body.")
        return False

    return True


@app.route('/release/<release_id>/packages/<package_id>/results', methods=['POST'])
def post_results(release_id, package_id):
    dbResults = DbResults(package_id, str(request.json))
    db.session.add(dbResults)
    db.session.commit()
    return ('', 204)
