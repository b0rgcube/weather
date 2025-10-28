FROM golang:1.21-alpine AS builder

WORKDIR /app

# Pre-cache modules
COPY go.mod go.sum* ./
RUN go mod download

# Copy source and build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o wms-server .

# Runtime image
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/wms-server .

EXPOSE 8080

CMD ["./wms-server"]
