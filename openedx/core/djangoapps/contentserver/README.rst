Status: Maintenance

Responsibilities
================
The contentserver app serves static course run assets such as images, PDFs, and audio files -- basically anything managed by Studio's "Files & Uploads" section. As part of this, it has to handle permissions checks, caching, and CDN configuration. It is unusual in that it's doing this all in middleware instead of having a dedicated view, which has led to a lot of confusion when finding it.

Direction: Convert to Blockstore
================================
Static file storage will eventually be moved to Blockstore.

Glossary
========

More Documentation
==================
