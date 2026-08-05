const CONFIG = Object.freeze({
  accountEmail: 'y-nakada@yn-factory.com',
  targetFolderId: '1doYv2SjuIgy421Kv_100-a2SCHYEHSRO',
  lookbackDays: 45,
  maxFilesPerRun: 40,
  copyRecordingFiles: false,
  sourceFolderNames: ['Meet Recordings'],
  titleKeywords: [
    'Meet',
    'Google Meet',
    'meeting notes',
    'transcript',
    'recording',
    '文字起こし',
    '議事録',
    '会議メモ'
  ],
  statePropertyKey: 'YN_GOOGLE_MEET_EXPORT_STATE_V1'
});

function setup() {
  const targetFolder = DriveApp.getFolderById(CONFIG.targetFolderId);
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'exportGoogleMeetArtifacts') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  ScriptApp.newTrigger('exportGoogleMeetArtifacts')
    .timeBased()
    .everyMinutes(5)
    .create();
  const result = exportGoogleMeetArtifacts();
  Logger.log(JSON.stringify({
    status: 'setup_complete',
    accountEmail: CONFIG.accountEmail,
    targetFolderName: targetFolder.getName(),
    targetFolderId: CONFIG.targetFolderId,
    initialRun: result
  }, null, 2));
}

function runNow() {
  const result = exportGoogleMeetArtifacts();
  Logger.log(JSON.stringify(result, null, 2));
}

function resetState() {
  PropertiesService.getScriptProperties().deleteProperty(CONFIG.statePropertyKey);
  Logger.log('State reset complete.');
}

function exportGoogleMeetArtifacts() {
  const targetFolder = DriveApp.getFolderById(CONFIG.targetFolderId);
  const state = loadState();
  const candidates = listCandidateFiles();
  const now = new Date();
  const results = {
    accountEmail: CONFIG.accountEmail,
    runAt: now.toISOString(),
    targetFolderId: CONFIG.targetFolderId,
    candidates: candidates.length,
    exported: [],
    skipped: [],
    errors: []
  };

  let processed = 0;
  candidates.forEach(item => {
    if (processed >= CONFIG.maxFilesPerRun) {
      return;
    }
    const file = item.file;
    const fileId = file.getId();
    const modifiedAt = safeDateIso(file.getLastUpdated());
    const previous = state[fileId];
    if (previous && previous.modifiedAt === modifiedAt) {
      results.skipped.push({ id: fileId, title: file.getName(), reason: 'already_exported' });
      return;
    }
    try {
      const exported = exportOneFile(file, targetFolder, item.sourceKind);
      state[fileId] = {
        modifiedAt,
        exportedAt: now.toISOString(),
        outputFolderId: exported.outputFolderId,
        outputFolderName: exported.outputFolderName,
        title: file.getName(),
        url: file.getUrl()
      };
      results.exported.push(exported);
      processed += 1;
    } catch (error) {
      results.errors.push({
        id: fileId,
        title: file.getName(),
        message: String(error && error.message ? error.message : error)
      });
    }
  });

  saveState(state);
  return results;
}

function listCandidateFiles() {
  const byId = {};
  CONFIG.sourceFolderNames.forEach(folderName => {
    const folders = DriveApp.searchFolders(
      "title = '" + escapeQuery(folderName) + "' and trashed = false"
    );
    while (folders.hasNext()) {
      collectFolderFiles(folders.next(), byId, 'source-folder:' + folderName, 0);
    }
  });

  const threshold = new Date(Date.now() - CONFIG.lookbackDays * 24 * 60 * 60 * 1000);
  const keywordQuery = CONFIG.titleKeywords
    .map(keyword => "title contains '" + escapeQuery(keyword) + "'")
    .join(' or ');
  const query = "trashed = false and modifiedDate > '" + toDriveDate(threshold) + "' and (" + keywordQuery + ')';
  const files = DriveApp.searchFiles(query);
  while (files.hasNext()) {
    const file = files.next();
    addCandidate(byId, file, 'title-search');
  }

  return Object.keys(byId)
    .map(id => byId[id])
    .sort((a, b) => b.file.getLastUpdated().getTime() - a.file.getLastUpdated().getTime());
}

function collectFolderFiles(folder, byId, sourceKind, depth) {
  const files = folder.getFiles();
  while (files.hasNext()) {
    addCandidate(byId, files.next(), sourceKind);
  }
  if (depth >= 2) {
    return;
  }
  const folders = folder.getFolders();
  while (folders.hasNext()) {
    collectFolderFiles(folders.next(), byId, sourceKind, depth + 1);
  }
}

function addCandidate(byId, file, sourceKind) {
  if (!isLikelyMeetArtifact(file, sourceKind)) {
    return;
  }
  byId[file.getId()] = { file, sourceKind };
}

function isLikelyMeetArtifact(file, sourceKind) {
  if (sourceKind.indexOf('source-folder:') === 0) {
    return true;
  }
  const name = file.getName().toLowerCase();
  return CONFIG.titleKeywords.some(keyword => name.indexOf(keyword.toLowerCase()) !== -1);
}

function exportOneFile(file, targetFolder, sourceKind) {
  const title = file.getName();
  const mimeType = file.getMimeType();
  const eventDate = inferEventDate(title, file.getDateCreated());
  const folderName = makeOutputFolderName(eventDate, title, file.getId());
  const outputFolder = targetFolder.createFolder(folderName);
  const text = readMeetText(file);
  const metadata = {
    title,
    date: formatDate(eventDate, 'yyyy-MM-dd'),
    start: '',
    end: '',
    participants: [],
    tags: ['google-meet', 'auto-import', 'y-nakada'],
    todo_candidates: [],
    source_url: file.getUrl(),
    source_id: file.getId(),
    source_kind: sourceKind,
    source_mime_type: mimeType,
    source_created_at: safeDateIso(file.getDateCreated()),
    source_modified_at: safeDateIso(file.getLastUpdated()),
    exported_at: new Date().toISOString(),
    exported_by: CONFIG.accountEmail,
    copy_recording_files: CONFIG.copyRecordingFiles
  };

  outputFolder.createFile('metadata.json', JSON.stringify(metadata, null, 2), MimeType.PLAIN_TEXT);
  outputFolder.createFile('source.url', '[InternetShortcut]\nURL=' + file.getUrl() + '\n', MimeType.PLAIN_TEXT);

  if (text) {
    outputFolder.createFile('meet-notes.txt', text, MimeType.PLAIN_TEXT);
  } else if (shouldCopyBlob(file)) {
    outputFolder.createFile(file.getBlob().copyBlob().setName(title));
  } else {
    outputFolder.createFile(
      'source-link.txt',
      'Text body was not exported. Check the source file:\n' + file.getUrl() + '\n',
      MimeType.PLAIN_TEXT
    );
  }

  return {
    sourceId: file.getId(),
    title,
    mimeType,
    outputFolderId: outputFolder.getId(),
    outputFolderName: folderName,
    outputFolderUrl: outputFolder.getUrl()
  };
}

function readMeetText(file) {
  const mimeType = file.getMimeType();
  if (mimeType === MimeType.GOOGLE_DOCS) {
    return DocumentApp.openById(file.getId()).getBody().getText();
  }
  if (isTextLike(file)) {
    return file.getBlob().getDataAsString('UTF-8');
  }
  return '';
}

function isTextLike(file) {
  const mimeType = file.getMimeType();
  const name = file.getName().toLowerCase();
  return mimeType.indexOf('text/') === 0 ||
    name.endsWith('.txt') ||
    name.endsWith('.md') ||
    name.endsWith('.vtt') ||
    name.endsWith('.srt') ||
    name.endsWith('.csv') ||
    name.endsWith('.json');
}

function shouldCopyBlob(file) {
  if (CONFIG.copyRecordingFiles) {
    return true;
  }
  const mimeType = file.getMimeType();
  return mimeType.indexOf('video/') !== 0 && mimeType.indexOf('audio/') !== 0;
}

function inferEventDate(title, fallbackDate) {
  const match = String(title).match(/(20\d{2})[-_./年 ]?(\d{1,2})[-_./月 ]?(\d{1,2})/);
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }
  return fallbackDate || new Date();
}

function makeOutputFolderName(date, title, fileId) {
  return formatDate(date, 'yyyyMMdd') + '-' + slugify(title) + '-' + fileId.slice(0, 8);
}

function slugify(value) {
  const normalized = String(value)
    .toLowerCase()
    .replace(/[^a-z0-9\u3040-\u30ff\u3400-\u9fff]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  return normalized.slice(0, 64) || 'google-meet';
}

function loadState() {
  const raw = PropertiesService.getScriptProperties().getProperty(CONFIG.statePropertyKey);
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    return {};
  }
}

function saveState(state) {
  PropertiesService.getScriptProperties().setProperty(
    CONFIG.statePropertyKey,
    JSON.stringify(state)
  );
}

function toDriveDate(date) {
  return Utilities.formatDate(date, 'UTC', "yyyy-MM-dd'T'HH:mm:ss");
}

function formatDate(date, pattern) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), pattern);
}

function safeDateIso(date) {
  return date ? date.toISOString() : '';
}

function escapeQuery(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}
