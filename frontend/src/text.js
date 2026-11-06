export function repairEncoding(value) {
  let result = value;
  for (let attempt = 0; attempt < 2 && /[ÃÂ]/.test(result); attempt += 1) {
    const bytes = Array.from(result, (character) => character.codePointAt(0));
    if (bytes.some((value) => value > 255)) break;
    try {
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(bytes));
      if (decoded === result) break;
      result = decoded;
    } catch {
      break;
    }
  }
  return result;
}
