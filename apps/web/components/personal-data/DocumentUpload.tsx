'use client';

import { useCallback, useRef, useState } from 'react';
import { Upload, X, FileText, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import axios from 'axios';

interface DocumentUploadProps {
  getUploadUrl: (filename: string) => Promise<{ uploadUrl: string; fileKey: string }>;
  onUploaded: (fileKey: string, filename: string) => void;
  accept?: string;
  maxSizeMb?: number;
  className?: string;
}

const DEFAULT_ACCEPT = '.pdf,.jpg,.jpeg,.png';
const DEFAULT_MAX_MB = 10;

export function DocumentUpload({
  getUploadUrl,
  onUploaded,
  accept = DEFAULT_ACCEPT,
  maxSizeMb = DEFAULT_MAX_MB,
  className,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (file.size > maxSizeMb * 1024 * 1024) {
        setError(`Файл слишком большой. Максимум ${maxSizeMb} МБ.`);
        return;
      }

      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
      if (!allowedTypes.includes(file.type)) {
        setError('Допустимые форматы: PDF, JPG, PNG.');
        return;
      }

      setUploading(true);
      setProgress(0);

      try {
        const { uploadUrl, fileKey } = await getUploadUrl(file.name);

        await axios.put(uploadUrl, file, {
          headers: { 'Content-Type': file.type },
          onUploadProgress: (evt) => {
            if (evt.total) {
              setProgress(Math.round((evt.loaded / evt.total) * 100));
            }
          },
        });

        setUploadedFile(file.name);
        onUploaded(fileKey, file.name);
      } catch {
        setError('Ошибка загрузки. Попробуйте ещё раз.');
      } finally {
        setUploading(false);
      }
    },
    [getUploadUrl, onUploaded, maxSizeMb]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) void handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
    e.target.value = '';
  };

  const clear = () => {
    setUploadedFile(null);
    setProgress(0);
    setError(null);
  };

  return (
    <div className={className}>
      {uploadedFile ? (
        <div className="flex items-center gap-3 px-4 py-3 bg-success-50 border border-success-200 rounded-xl">
          <FileText className="w-5 h-5 text-success-600 flex-shrink-0" />
          <span className="flex-1 text-sm text-success-800 truncate">{uploadedFile}</span>
          <button
            type="button"
            onClick={clear}
            className="p-1 rounded-lg hover:bg-success-100 transition-colors"
          >
            <X className="w-4 h-4 text-success-600" />
          </button>
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={clsx(
            'flex flex-col items-center justify-center gap-2 px-4 py-6 rounded-xl border-2 border-dashed cursor-pointer transition-colors',
            isDragging
              ? 'border-accent-500 bg-accent-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400 hover:bg-gray-100'
          )}
        >
          {uploading ? (
            <>
              <Loader2 className="w-6 h-6 text-accent-500 animate-spin" />
              <p className="text-sm text-gray-600">Загрузка… {progress}%</p>
              <div className="w-full max-w-xs h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-500 transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </>
          ) : (
            <>
              <Upload className="w-6 h-6 text-gray-400" />
              <p className="text-sm text-gray-600 text-center">
                Перетащите файл или{' '}
                <span className="text-accent-600 font-medium">выберите</span>
              </p>
              <p className="text-xs text-gray-400">PDF, JPG, PNG · до {maxSizeMb} МБ</p>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept={accept}
            className="hidden"
            onChange={handleChange}
          />
        </div>
      )}

      {error && <p className="mt-1.5 text-xs text-danger-600">{error}</p>}
    </div>
  );
}
