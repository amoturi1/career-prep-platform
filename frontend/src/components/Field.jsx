// A labelled form field with an accessible error message (NFR-04, NFR-05).
import { forwardRef } from "react";

const Field = forwardRef(function Field(
  { id, label, error, hint, as = "input", required, full, children, ...props },
  ref
) {
  const Control = as;
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`field${error ? " field-invalid" : ""}${full ? " span-2" : ""}`}>
      <label htmlFor={id}>
        {label}
        {required && <span className="required" aria-hidden="true"> *</span>}
      </label>
      {hint && (
        <p id={`${id}-hint`} className="field-hint">
          {hint}
        </p>
      )}
      <Control ref={ref} id={id} name={id} aria-invalid={Boolean(error)} aria-describedby={describedBy}
        required={required} {...props}>
        {children}
      </Control>
      {error && (
        <p id={`${id}-error`} className="field-error">
          {error}
        </p>
      )}
    </div>
  );
});

export default Field;
