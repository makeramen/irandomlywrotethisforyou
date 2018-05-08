package main

import (
	"bytes"
	"compress/gzip"
	"encoding/gob"

	"google.golang.org/appengine/memcache"
)

var (
	gzipGob = memcache.Codec{Marshal: gzipGobMarhsal, Unmarshal: gzipGobUnMarhsal}
)

func gzipGobMarhsal(v interface{}) ([]byte, error) {
	var gobBuf bytes.Buffer
	if err := gob.NewEncoder(&gobBuf).Encode(v); err != nil {
		return nil, err
	}
	var gzipBuf bytes.Buffer
	w := gzip.NewWriter(&gzipBuf)
	if _, err := w.Write(gobBuf.Bytes()); err != nil {
		return nil, err
	}
	w.Close()
	return gzipBuf.Bytes(), nil
}

func gzipGobUnMarhsal(data []byte, v interface{}) error {
	r, err := gzip.NewReader(bytes.NewBuffer(data))
	if err != nil {
		return err
	}
	return gob.NewDecoder(r).Decode(v)
}
