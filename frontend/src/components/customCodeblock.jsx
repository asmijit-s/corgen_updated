import { useRef } from 'react';
import { ClipboardDocumentIcon } from '@heroicons/react/24/outline';

const CodeBlockWithCopy = ({ node }) => {
  const codeRef = useRef(null);

  const copyToClipboard = () => {
    if (codeRef.current) {
      navigator.clipboard.writeText(codeRef.current.textContent);
    }
  };

  return (
    <div className="code-block">
      <pre ref={codeRef}>
        <code>{node.content.content[0].text}</code>
      </pre>
      <button className="code-block-copy" onClick={copyToClipboard}>
        <ClipboardDocumentIcon className="w-4 h-4" />
        Copy
      </button>
    </div>
  );
};

export default CodeBlockWithCopy;