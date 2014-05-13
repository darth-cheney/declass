# APIv2 -- JSON Spec
This draft document sets out a standard for the data format that should be returned by the Declass API (v2). Regardless of the type of query, the database or collection being queried, or the optional parameters provided in a request, the API should always respond with a JSON object that fits either the **success** or **error** types, described below.


### Return Type: `success`
If a call to the API does not result in an error, a `success` object is returned. At minimum, a `result` object, which is only named here as a formality, should contain:
* `count` - An integer corresponding to the number of results
* `results` - An array of result objects (see example)
* `page` - An integer corresponding to the page number of the current query. Will be `0` if pagination is not used in the request/response.

The objects in the `results` array should contain key/value pairs corresponding to the types of data requested. For example, if one sends a request to the `foo` collection to get all information about all documents published after 1979 at `/api/foo/documents?date=>1979`:
```javascript
{
  count: 3,
  results: [
    {
      id: 28674,
      title: 'Fake Document 28674',
      body: // Some text,
      date: '01-01-1983'
    },
    {
      id: 987,
      title: 'Fake Document 987',
      body: // Some text,
      date: '7-24-1981'
    },
    {
      id: 3,
      title: 'Fake Document 3',
      body: // some text,
      date: '03-01-1987'
    }
  ],
  page: 0
}
```
If `results` is always an array, then anyone dealing with the data will have a standard way of parsing it across functions. Even if the initial request makes use of a function called `.findOne()`, the `success` object should still return `results` as an array:
```javascript
{
  count: 1,
  results: [
    {
      id: 6754,
      title: 'Fake Document 6754',
      body: //Some text,
      date: '01-01-1968'
    }
  ],
  page: 0
}
```
This ensures that developers on the front end and people regularly interacting with the JSON data have a consistent way to implement their methods for parsing.


### Return Type: `error`
If a call to the API results in an error, most of the time this will manifest itself as an HTTP error. The API should be able to generate the appropriate HTTP response codes for a given request and popualte an `error` object with these codes. The response object should be able to accomodate both HTTP response codes that are errors (ie, a `404` or `500`) in addition to any custom errors introduced by the programming in the API itself. Thus, the following attributes are required, at minimum:
* `error` - An object that is set when there is an HTTP error of some kind. It has the following key/values:
  * `code` - Value is an integer corresponding to an HTTP response code.
  * `message` - Value is a string corresponding to a custom error message delivered for the given HTTP code. Should be an empty string if not used.
* `apiErrors` - Array of `apiError` objects, which themselves also have two key/value pairs:
  * `apiError` - A string describing the error. This can be the textual version of some kind of Exception, or anything else that the API has set as a standard set of errors that are something other than HTTP response errors.
  * `message` - A string corresponding to some custom message, perhaps a more verbose explanation of the error or stack callback (in dev environments). Should be an empty string if not used.

In this example, the API returns a simple `404` HTTP Response.
```javascript
{
  error: {
    code: 404,
    message: 'Resource Not Found'
  },
  apiErrors: []
}
```

In this example, the HTTP Response was OK, but there was an Exception thrown at some point while interacting with the database:
```javascript
{
  error: {},
  apiErrors: [
    {
      apiError: 'DBException',
      message: 'You do not have write permissions on the database /foo_db/'
    }
  ]
}
```

And in this final case, there was both a series of `apiErrors` which themselves resulted in an HTTP error for some reason.
```javascript
{
  error: {
    code: 500,
    message: ''
  },
  apiErrors: [
    {
      apiError: 'IOError',
      message: 'There was an error opening the SQLite database for writing'
    },
    {
      apiError: 'ParseError',
      message: 'Cannot call function .write() of undefined'
    }  
  ]
}
```
### On 'Minimum' Requirements
These are only minimum requirements. We should be able to add whatever attributes we want on a case by case basis. For example, when using pagination, it might be a good idea to return the URL and querystring for the 'next' page. In the example below, the response returns pages of size `25`, is on page `2` of that query, and has a new attribute `nextPage` that points to the next URL to follow:
```javascript
{
  count: 25,
  results: [
    {
      id: 1,
      title: 'Title 1'
    },
    {
      id: 2,
      title: 'Title 2'
    },
    // 
    // And so on for 23 more
    //
  ],
  page: 2,
  nextPage: 'http://www.example.com/api/collection/document/search?page=3&criteria1=x&criteria2=y'
}
```
Now imagine a use case in a program or in the front-end of the site:
```javascript
function doStuff() {
  result = fetchAPIData(url);
  while(result.page > 0) {
    processResults(result); // Do whatever processing on the data you need to do
    result = fetchAPIData(result.nextPage); // Fetches the next page automatically and updates the variable
  }
}
```


## Questions

* Should we include a `response` attribute on every `success` object that corresponds to successful HTTP codes?
* Should `apiErrors` only be required when the API is in development mode, and excluded from a public-facing API?
* Any suggestions for changing / problems with this structure?

#### NOTE
The requirements have shied away from using things like `undefined`, `null`, `true`, and `false` as values because, according to some (older) JSON parsers, these are not valid JSON attributes. I'm certainly open to changing this, as it would make things much easier to read and test. Let me know your thoughts.
