const INPUT_BOX_FOLDER_ID = '1BMtWrI2mklfTVLOQHPQm75ffxTM0MBSy';

function doGet() {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('YNFactory Input Upload')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function uploadInput(payload) {
  if (!INPUT_BOX_FOLDER_ID || INPUT_BOX_FOLDER_ID === 'PASTE_INPUT_BOX_FOLDER_ID_HERE') {
    throw new Error('INPUT_BOX_FOLDER_ID is not configured.');
  }

  const root = DriveApp.getFolderById(INPUT_BOX_FOLDER_ID);
  const now = new Date();
  const timestamp = Utilities.formatDate(now, 'Asia/Tokyo', 'yyyyMMdd-HHmmss');
  const title = payload.title || (payload.files && payload.files[0] ? payload.files[0].name : 'input');
  const inputId = `${timestamp}-${slugify_(title)}`;
  const folder = root.createFolder(inputId);
  const filesFolder = folder.createFolder('files');

  const noteParts = [];
  if (payload.text) noteParts.push(payload.text);
  if (payload.url) noteParts.push(payload.url);
  if (noteParts.length) {
    folder.createFile('note.md', noteParts.join('\n\n') + '\n', MimeType.PLAIN_TEXT);
  }

  const savedFiles = [];
  (payload.files || []).forEach(file => {
    const bytes = Utilities.base64Decode(file.base64);
    const blob = Utilities.newBlob(bytes, file.mimeType || 'application/octet-stream', sanitizeFilename_(file.name));
    const saved = filesFolder.createFile(blob);
    savedFiles.push(`files/${saved.getName()}`);
  });

  const metadata = {
    title,
    tags: splitWords_(payload.tags),
    priority: payload.priority || 'normal',
    related_project: payload.relatedProject || '',
    todo_candidate: payload.todoCandidate === true,
    todo_candidates: splitLines_(payload.todoCandidates),
    notes: 'google_apps_script_uploader',
    uploaded_at: now.toISOString(),
    saved_files: savedFiles
  };
  folder.createFile('metadata.json', JSON.stringify(metadata, null, 2), MimeType.PLAIN_TEXT);

  return { ok: true, inputId };
}

function slugify_(value) {
  const slug = String(value || 'input')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 48);
  return slug || 'input';
}

function sanitizeFilename_(value) {
  return String(value || 'upload.bin').replace(/[\\/:*?"<>|]+/g, '-');
}

function splitWords_(value) {
  return String(value || '').split(/[\s,#]+/).map(s => s.trim()).filter(Boolean);
}

function splitLines_(value) {
  return String(value || '').split(/\r?\n/).map(s => s.trim()).filter(Boolean);
}
