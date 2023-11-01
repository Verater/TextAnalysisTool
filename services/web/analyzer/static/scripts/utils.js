
'use strict';

const HTTP_OK = 200;

const Color = {
  WHITE: 'rgb(255,255,255)',
  GREY32: 'rgb(32,32,32)',
  GREY64: 'rgb(64,64,64)',
};
Object.freeze(Color);


function ifPrimaryClick(e, func) {
  if (e.button === 0) {
    func(e);
  }
}


function ifEnterPressed(e, func) {
  if (e.key === 'Enter') {
    func(e);
  }
}

function ifEscPressed(e, func) {
  if (e.key === 'Escape') {
    func(e);
  }
}



const px = value => value + 'px';


function emptyElement(element) {
  const numNodesToRemove = element.childElementCount;
  for (let i = 0; i < numNodesToRemove; i++) {
    element.removeChild(element.childNodes[0]);
  }
}


function isIterable(obj) {
  // checks for null and undefined
  if (obj === null) {
    return false;
  }
  return typeof obj[Symbol.iterator] === 'function';
}


function objHasEntries(obj) {
  for (const x in obj) {
    return true;
  }
  return false;
}


function hide(element) {
  element.style.display = 'none';
}


function show(element) {
  element.style.display = 'block';
}

function createElement(tag, args) {
  const e = document.createElement(tag);

  if (args.cls) {
    if (typeof args.cls === 'string') {
      args.cls = [args.cls];
    }

    for (const className of args.cls) {
      e.classList.add(className);
    }

    delete args.cls;
  }
