-- AI-Powered Syllabus Generation System - Database Schema
-- PostgreSQL Migration Script

-- Drop existing tables if they exist (for clean migrations)
DROP TABLE IF EXISTS syllabus_elo_mapping CASCADE;
DROP TABLE IF EXISTS syllabus_performance_mapping CASCADE;
DROP TABLE IF EXISTS syllabus_tlo_mapping CASCADE;
DROP TABLE IF EXISTS syllabi CASCADE;
DROP TABLE IF EXISTS elo_performance_mapping CASCADE;
DROP TABLE IF EXISTS elos CASCADE;
DROP TABLE IF EXISTS performance_tlo_mapping CASCADE;
DROP TABLE IF EXISTS performances CASCADE;
DROP TABLE IF EXISTS tlos CASCADE;
DROP TABLE IF EXISTS organization_profiles CASCADE;

-- Organization Profiles Table
CREATE TABLE organization_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_text TEXT NOT NULL,
    summary TEXT NOT NULL,
    context_overview TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL
);

-- Terminal Learning Objectives (TLOs) Table
CREATE TABLE tlos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organization_profiles(id) ON DELETE CASCADE,
    course_type VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_selected BOOLEAN DEFAULT FALSE
);

-- Performance Objectives Table
CREATE TABLE performances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_selected BOOLEAN DEFAULT FALSE
);

-- Performance-TLO Mapping Table (Many-to-Many)
CREATE TABLE performance_tlo_mapping (
    performance_id UUID REFERENCES performances(id) ON DELETE CASCADE,
    tlo_id UUID REFERENCES tlos(id) ON DELETE CASCADE,
    PRIMARY KEY (performance_id, tlo_id)
);

-- Enabling Learning Objectives (ELOs) Table
CREATE TABLE elos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    is_selected BOOLEAN DEFAULT FALSE
);

-- ELO-Performance Mapping Table (Many-to-Many)
CREATE TABLE elo_performance_mapping (
    elo_id UUID REFERENCES elos(id) ON DELETE CASCADE,
    performance_id UUID REFERENCES performances(id) ON DELETE CASCADE,
    PRIMARY KEY (elo_id, performance_id)
);

-- Syllabi Table
CREATE TABLE syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    org_id UUID NOT NULL REFERENCES organization_profiles(id) ON DELETE CASCADE,
    course_type VARCHAR(100) NOT NULL,
    document_content BYTEA NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Syllabus-TLO Mapping Table
CREATE TABLE syllabus_tlo_mapping (
    syllabus_id UUID REFERENCES syllabi(id) ON DELETE CASCADE,
    tlo_id UUID REFERENCES tlos(id) ON DELETE CASCADE,
    PRIMARY KEY (syllabus_id, tlo_id)
);

-- Syllabus-Performance Mapping Table
CREATE TABLE syllabus_performance_mapping (
    syllabus_id UUID REFERENCES syllabi(id) ON DELETE CASCADE,
    performance_id UUID REFERENCES performances(id) ON DELETE CASCADE,
    PRIMARY KEY (syllabus_id, performance_id)
);

-- Syllabus-ELO Mapping Table
CREATE TABLE syllabus_elo_mapping (
    syllabus_id UUID REFERENCES syllabi(id) ON DELETE CASCADE,
    elo_id UUID REFERENCES elos(id) ON DELETE CASCADE,
    PRIMARY KEY (syllabus_id, elo_id)
);

-- Performance Optimization Indexes
CREATE INDEX idx_tlos_org_id ON tlos(org_id);
CREATE INDEX idx_tlos_course_type ON tlos(course_type);
CREATE INDEX idx_tlos_is_selected ON tlos(is_selected);
CREATE INDEX idx_performances_is_selected ON performances(is_selected);
CREATE INDEX idx_elos_is_selected ON elos(is_selected);
CREATE INDEX idx_syllabi_session_id ON syllabi(session_id);
CREATE INDEX idx_syllabi_org_id ON syllabi(org_id);
CREATE INDEX idx_performance_tlo_mapping_tlo_id ON performance_tlo_mapping(tlo_id);
CREATE INDEX idx_elo_performance_mapping_performance_id ON elo_performance_mapping(performance_id);
