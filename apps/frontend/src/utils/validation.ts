/*
 * File validation utilities
 */

const MAX_FILENAME_LENGTH = 255;
const DANGEROUS_CHARS = /[<>:"/\\|?*\x00-\x1f]/g;
const WINDOWS_RESERVED_NAMES = new Set([
  'con',
  'prn',
  'aux',
  'nul',
  'com1',
  'com2',
  'com3',
  'com4',
  'com5',
  'com6',
  'com7',
  'com8',
  'com9',
  'lpt1',
  'lpt2',
  'lpt3',
  'lpt4',
  'lpt5',
  'lpt6',
  'lpt7',
  'lpt8',
  'lpt9',
]);

export function validateFilename(filename: string): [boolean, string | null] {
  if (!filename) {
    return [false, 'Filename cannot be empty'];
  }

  if (!filename.trim()) {
    return [false, 'Filename cannot be empty or whitespace only'];
  }

  if (new TextEncoder().encode(filename).length > MAX_FILENAME_LENGTH) {
    return [false, `Filename too long (max ${MAX_FILENAME_LENGTH} bytes)`];
  }

  if (filename.includes('..')) {
    return [false, 'Filename cannot contain directory traversal sequences'];
  }

  if (DANGEROUS_CHARS.test(filename)) {
    return [false, 'Filename contains invalid characters (< > : " / \\ | ? *)'];
  }

  const nameWithoutExt =
    filename.split('.').slice(0, -1).join('.') || filename.split('.')[0];
  if (WINDOWS_RESERVED_NAMES.has(nameWithoutExt.toLowerCase())) {
    return [false, 'Filename uses a reserved system name'];
  }

  if (
    filename.startsWith('.') ||
    filename.endsWith('.') ||
    filename.startsWith(' ')
  ) {
    return [false, "Filename cannot start with '.' or ' '"];
  }

  return [true, null];
}

export function sanitizeFilename(filename: string): string {
  if (!filename) {
    return 'unnamed_file';
  }

  let sanitized = filename.replace(DANGEROUS_CHARS, '_');

  const parts = sanitized.split('.');
  const nameWithoutExt = parts.slice(0, -1).join('.') || parts[0];
  if (WINDOWS_RESERVED_NAMES.has(nameWithoutExt.toLowerCase())) {
    parts[0] = `_${parts[0]}`;
    sanitized = parts.join('.');
  }

  sanitized = sanitized.replace(/^[\.\s]+|[\.\s]+$/g, '');

  if (!sanitized || sanitized.startsWith('.')) {
    const ext = parts.length > 1 ? `.${parts[parts.length - 1]}` : '';
    sanitized = `file${ext}` || 'unnamed_file';
  }

  return sanitized;
}

export function truncateFilename(
  filename: string,
  maxLength: number = MAX_FILENAME_LENGTH
): string {
  const encodedLength = new TextEncoder().encode(filename).length;
  if (encodedLength <= maxLength) {
    return filename;
  }

  const parts = filename.split('.');
  if (parts.length === 1) {
    return filename.substring(0, maxLength);
  }

  const ext = `.${parts[parts.length - 1]}`;
  const extBytes = new TextEncoder().encode(ext).length;
  const availableBytes = maxLength - extBytes - 3;

  if (availableBytes <= 0) {
    return `file${ext.substring(0, maxLength - 4)}` || 'file';
  }

  let baseName = parts.slice(0, -1).join('.');
  while (
    new TextEncoder().encode(baseName).length > availableBytes &&
    baseName.length > 1
  ) {
    baseName = baseName.substring(0, baseName.length - 1);
  }

  if (baseName.length < parts.slice(0, -1).join('.').length) {
    baseName += '...';
  }

  const result = `${baseName}${ext}`;

  if (new TextEncoder().encode(result).length > maxLength) {
    return result.substring(0, maxLength);
  }

  return result;
}
