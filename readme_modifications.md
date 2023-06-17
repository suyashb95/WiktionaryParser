### Some notes on the modifications made by bjkeefe to `core.py`

#### Motivation

I had been happily using WiktionaryParser for several months.  One day, I was developing
an application where I wanted to be able to distinguish between two cases: (1) where
Wiktionary does not have any English definitions for a given word, and (2) where
Wiktionary does not have any entry at all.

I made a few modifications to `core.py` to support this desire.  The returned value
remains a `list`, containg a `dict`, in all cases.  If the `word` and `language` passed to
`.fetch()` yield a Wiktionary entry, the results will be the same as before.

#### So, what's new?

If there is no entry for a given `word` and `language`, the returned value is now no
longer an empty `list`, but a `list`, containing a `dict`, whose only key is
`"additional_info"`, whose value is a `str`: `"no <language> entry for <word>".`

If there is no entry at all, same as above, except the value in the `dict` becomes
`"Wiktionary does not yet have an entry for <word>"`.


#### Source code differences

Here is the diff output (ignoring whitespace) between the new version and the original:

```
$ diff -w core.py core.py.abo
119c119
<                 return [{"additional_info": f"no {language} entry for {self.current_word}"}]
---
>                 return []
126c126
<                 return [{"additional_info": f"no {language} entry for {self.current_word}"}]
---
>                 return []
285,288d284
<         search_string = "Wiktionary does not yet have an entry for " + word
<         result = self.soup.find_all(string=re.compile(search_string))
<         if result:
<             return [{"additional_info": search_string}]
```

#### Testing

The new version of `core.py` passes all tests in `tests/test_core.py.`

Because I didn't have time to modify the existing tests, I wrote some quick tests that
explicitly test the modifications I made.  These are in `tests/test_core_new.py`.  This
file expects to be run with `pytest`, because I am less familiar with `unittest`.  All of
the tests pass when run against the new version of `core.py`.

NB: the new tests will NOT all pass if run against the old version of `core.py.`

Also, I wrote a little script called `driver.py`.  This is intended for interactive testing.

```
$ py driver.py -h
usage: driver.py [-h] [-m] word

Check <word> against Wiktionary using WiktionaryParser

positional arguments:
  word                  the word to look up

options:
  -h, --help            show this help message and exit
  -m, --multiple-languages
                        if present, look up <word> for several languages; otherwise, just English
```

#### Organization

All of the above -- the modifications and new files -- are in a new `git` branch named
`additional_info`.

#### Minor problem with backwards compatibility

If someone has written some code that checks the result returned by `.fetch()` like this ...

```
result = parser.fetch(word)
if not result:     # --or--  if len(result) == 0:
    do_something()
```

... this will no longer work.  This could be changed to, for example:

```
result = parser.fetch(word)
if not "definitions" in result[0]:
    do_something()
```


#### Questions, comments, criticisms

Please feel free to email me: bjkeefe@gmail.com.  Thanks for reading!
