"""Small backend-neutral primitives for explicitly managed entity cleanup."""

from django.db import connections


def delete_id_direct(model, identifier):
    """Delete one known key without Django's relational cascade collector.

    Callers must delete dependants first. Firestore has no server-side foreign
    keys, and django-gcloud-connectors 1.5 can report a cascaded parent delete
    as successful without removing that parent. Its key-only DELETE query also
    misses some constrained entities, so use the connector's key primitive for
    Firestore and Django's direct command elsewhere.
    """
    alias = model.objects.db
    database = connections[alias]
    if database.settings_dict["ENGINE"].startswith("gcloudc.db.backends."):
        database.ensure_connection()
        key = database.connection.new_key(
            model._meta.db_table,
            identifier,
            namespace=getattr(database, "namespace", None),
        )
        existed = database.connection.get(key) is not None
        if existed:
            database.connection.delete(key)
        return int(existed)
    return model.objects.filter(pk=identifier)._raw_delete(alias)


def delete_ids_direct(model, identifiers):
    deleted = 0
    for identifier in identifiers:
        deleted += delete_id_direct(model, identifier)
    return deleted
