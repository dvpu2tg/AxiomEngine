// t09 — A MEMBER DECLARED IN A TYPE LITERAL (issue #39). `options.getValue()` below resolves, in
// the checker, to the signature inside the `& { … }` literal, which belongs to no container. The
// declared target is the member of the receiver's APPARENT type — `Options#getValue` — and where
// no real container declares it, the site is `indirect`, never a phantom method on the class
// that happens to enclose the cast.

export class Options {
  getValue(name: string): unknown { return name; }
  setValue(name: string, value: unknown): void { void name; void value; }
}

export class ArgumentsReader {
  read(container: Options): unknown {
    const options = container as Options & {
      setValue(name: string, value: unknown): void;
      getValue(name: string): unknown;
    };
    options.setValue("a", 1);
    return options.getValue("a");                       // -> Options#getValue, not ArgumentsReader#getValue
  }
}

export class Serializer {
  toObject(value: { toObject(serializer: Serializer): unknown } | undefined): unknown {
    return value ? value.toObject(this) : undefined;    // indirect: no container declares this member
  }
}
