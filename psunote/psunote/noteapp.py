import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    db = models.db
    form = forms.NoteForm()

    form.existing_tags.choices = [(tag.id, tag.name) for tag in models.Tag.query.all()]

    if form.validate_on_submit():
        note = models.Note(
            title=form.title.data,
            description=form.description.data,
            tags=[],
        )

        if form.new_tag.data.strip():
            tag = models.Tag(name=form.new_tag.data.strip())
            db.session.add(tag)
            note.tags.append(tag)
        elif form.existing_tags.data:
            tag = models.Tag.query.get(form.existing_tags.data)
            if tag:
                note.tags.append(tag)

        db.session.add(note)
        db.session.commit()

        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-create.html", form=form)


@app.route("/notes/edit/<note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = models.Note.query.get_or_404(note_id)
    form = forms.NoteForm(obj=note)

    form.existing_tags.choices = [(tag.id, tag.name) for tag in models.Tag.query.all()]

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data

        tag = models.Tag.query.get(form.existing_tags.data)
        if tag:
            note.tags = [tag]

        db.session.commit()

        return flask.redirect(flask.url_for("index"))

    form.existing_tags.data = [tag.id for tag in note.tags][0] if note.tags else None

    return flask.render_template("notes-edit.html", form=form, note=note)


@app.route("/notes/delete/<note_id>", methods=["GET", "POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.get(models.Note, note_id)
    if note:
        db.session.delete(note)
        db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/delete/<tag_id>", methods=["GET", "POST"])
def tags_delete(tag_id):
    db = models.db
    tag = db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id)).scalars().first()
    if tag:
        notes = (
            db.session.execute(
            db.select(models.Note).join(models.note_tag_m2m).where(models.note_tag_m2m.c.tag_id == tag_id)
        ).scalars().fetchall()
        )
        for note in notes:
            note.tags.remove(tag)
        db.session.delete(tag)
        db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


if __name__ == "__main__":
    app.run(debug=True)
