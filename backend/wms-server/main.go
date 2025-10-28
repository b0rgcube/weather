package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"net/url"
	"os"
	"path"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"
)

type Config struct {
	DataDir string
	Port    string
}

var config Config

func init() {
	config = Config{
		DataDir: getEnv("DATA_DIR", "/data/weather"),
		Port:    getEnv("PORT", "8080"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":  "healthy",
		"service": "weather-wms-server",
		"time":    time.Now().UTC().Format(time.RFC3339),
		"config": map[string]string{
			"dataDir": config.DataDir,
			"port":    config.Port,
		},
	})
}

func wmsHandler(w http.ResponseWriter, r *http.Request) {
	request := r.URL.Query().Get("REQUEST")
	vars := mux.Vars(r)
	dataset := vars["dataset"]
	log.Printf("WMS Request: %s, dataset: %s", request, dataset)

	switch request {
	case "GetCapabilities":
		handleGetCapabilities(w, r, dataset)
	case "GetMap":
		handleGetMap(w, r, dataset)
	case "GetFeatureInfo":
		handleGetFeatureInfo(w, r, dataset)
	default:
		http.Error(w, "Invalid REQUEST parameter. Use GetCapabilities, GetMap, or GetFeatureInfo", http.StatusBadRequest)
	}
}

func handleGetCapabilities(w http.ResponseWriter, r *http.Request, dataset string) {
	w.Header().Set("Content-Type", "text/xml")

	// Generate a simple time dimension list: now to +48h in 3h steps
	times := make([]string, 0, 17)
	now := time.Now().UTC().Truncate(time.Hour)
	for i := 0; i <= 48; i += 3 {
		t := now.Add(time.Duration(i) * time.Hour)
		times = append(times, t.Format(time.RFC3339))
	}
	timeList := strings.Join(times, ",")

	// Basic capabilities including a time Dimension
	fmt.Fprintf(w, `<?xml version="1.0" encoding="UTF-8"?>
<WMS_Capabilities version="1.3.0" xmlns="http://www.opengis.net/wms">
  <Service>
    <Name>WMS</Name>
    <Title>Weather Visualization WMS Server</Title>
    <Abstract>Custom Golang WMS server for NOAA GFS weather data</Abstract>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>text/xml</Format>
      </GetCapabilities>
      <GetMap>
        <Format>image/png</Format>
      </GetMap>
      <GetFeatureInfo>
        <Format>application/json</Format>
      </GetFeatureInfo>
    </Request>
    <Layer>
      <Title>Weather Data Layers</Title>
      <CRS>EPSG:4326</CRS>
      <CRS>EPSG:3857</CRS>
      <Dimension name="time" units="ISO8601">%s</Dimension>
    </Layer>
  </Capability>
</WMS_Capabilities>`, timeList)
}

func handleGetMap(w http.ResponseWriter, r *http.Request, dataset string) {
	q := r.URL.Query()

	// Dimensions
	width, _ := strconv.Atoi(q.Get("WIDTH"))
	height, _ := strconv.Atoi(q.Get("HEIGHT"))
	if width <= 0 {
		width = 256
	}
	if height <= 0 {
		height = 256
	}

	// Parse dataset path to get layer (param name) and file name
	// Expected: weather/<layer>/<file>.nc (e.g., weather/temp_2m/temp_2m_YYYYMMDDHH.nc)
	layer := ""
	file := ""
	if dataset != "" {
		parts := strings.Split(dataset, "/")
		if len(parts) >= 2 {
			layer = parts[len(parts)-2]
			file = parts[len(parts)-1]
		} else if len(parts) == 1 {
			file = parts[0]
		}
	}
	// Fallback: allow LAYERS param to map to our logical layer if needed
	if layer == "" {
		if l := q.Get("LAYERS"); l != "" {
			layer = l
		}
	}
	// Normalize file to base name only
	if file != "" {
		file = path.Base(file)
	}

	// Map WMS BBOX/CRS -> processor bbox (EPSG:4326)
	bbox := q.Get("BBOX")
	crs := q.Get("CRS")
	if crs == "" {
		// Some clients use SRS
		crs = q.Get("SRS")
	}

	var bbox4326 string
	if bbox != "" {
		parts := strings.Split(bbox, ",")
		if len(parts) == 4 {
			minx, _ := strconv.ParseFloat(parts[0], 64)
			miny, _ := strconv.ParseFloat(parts[1], 64)
			maxx, _ := strconv.ParseFloat(parts[2], 64)
			maxy, _ := strconv.ParseFloat(parts[3], 64)

			// If WebMercator, convert to lon/lat
			if strings.EqualFold(crs, "EPSG:3857") || strings.EqualFold(crs, "EPSG:900913") {
				m2lon := func(mx float64) float64 { return (mx / 6378137.0) * 180.0 / math.Pi }
				m2lat := func(my float64) float64 { return (2*math.Atan(math.Exp(my/6378137.0)) - math.Pi/2) * 180.0 / math.Pi }
				lon1 := m2lon(minx)
				lat1 := m2lat(miny)
				lon2 := m2lon(maxx)
				lat2 := m2lat(maxy)
				minx, miny, maxx, maxy = lon1, lat1, lon2, lat2
			}
			bbox4326 = fmt.Sprintf("%f,%f,%f,%f", minx, miny, maxx, maxy)
		}
	}

	// Map optional params
	timeParam := q.Get("TIME")
	colorRange := q.Get("COLORSCALERANGE")
	styles := q.Get("STYLES")
	palette := q.Get("PALETTE")
	gammaParam := q.Get("GAMMA")
	if gammaParam == "" {
		gammaParam = q.Get("gamma")
	}

	// Build processor render URL
	v := url.Values{}
	if layer != "" {
		v.Set("layer", layer)
	}
	if file != "" {
		v.Set("file", file)
	}
	v.Set("width", strconv.Itoa(width))
	v.Set("height", strconv.Itoa(height))
	if bbox4326 != "" {
		v.Set("bbox", bbox4326)
	}
	if colorRange != "" {
		v.Set("colorscalerange", colorRange)
	}
	if timeParam != "" {
		v.Set("time", timeParam)
	}
	// Forward style/palette to processor for high-contrast rendering
	if styles != "" {
		v.Set("styles", styles)
	} else if palette != "" {
		v.Set("palette", palette)
	}
	// Forward gamma (contrast tuning) if provided
	if gammaParam != "" {
		v.Set("gamma", gammaParam)
	}

	renderURL := "http://weather-processor:8081/api/render?" + v.Encode()
	resp, err := http.Get(renderURL)
	if err != nil {
		http.Error(w, fmt.Sprintf("render backend error: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		w.WriteHeader(http.StatusBadGateway)
		io.Copy(w, resp.Body)
		return
	}

	// Stream PNG back to client
	w.Header().Set("Content-Type", "image/png")
	io.Copy(w, resp.Body)
}

func handleGetFeatureInfo(w http.ResponseWriter, r *http.Request, dataset string) {
	w.Header().Set("Content-Type", "application/json")
	// Minimal stub response
	json.NewEncoder(w).Encode(map[string]interface{}{
		"dataset": dataset,
		"value":   nil,
		"info":    "FeatureInfo not implemented yet",
	})
}

func main() {
	log.Printf("Starting Weather WMS Server on port %s", config.Port)

	router := mux.NewRouter()
	router.HandleFunc("/health", healthHandler).Methods("GET")
	router.HandleFunc("/wms", wmsHandler).Methods("GET", "HEAD", "OPTIONS")
	router.HandleFunc("/wms/{dataset:.*}", wmsHandler).Methods("GET", "HEAD", "OPTIONS")

	handler := cors.New(cors.Options{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "HEAD", "OPTIONS"},
		AllowedHeaders: []string{"*"},
	}).Handler(router)

	if err := http.ListenAndServe(":"+config.Port, handler); err != nil {
		log.Fatal(err)
	}
}
