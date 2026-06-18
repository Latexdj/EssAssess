const key = (assignmentId: string) => `essay_draft_${assignmentId}`;

export const draftStorage = {
  save: (assignmentId: string, text: string) => {
    try {
      localStorage.setItem(key(assignmentId), text);
    } catch {
      // storage quota exceeded — fail silently
    }
  },

  load: (assignmentId: string): string => {
    try {
      return localStorage.getItem(key(assignmentId)) ?? "";
    } catch {
      return "";
    }
  },

  clear: (assignmentId: string) => {
    try {
      localStorage.removeItem(key(assignmentId));
    } catch {
      // ignore
    }
  },
};
